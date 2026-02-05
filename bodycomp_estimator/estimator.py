from __future__ import annotations

from dataclasses import asdict

import numpy as np

from .features import compute_features, feature_quality_heuristic
from .pose import PoseLandmarks
from .schemas import EstimateResult, SubjectMetadata


def _clamp(x: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, x)))


def estimate_body_fat_percent(pose: PoseLandmarks, meta: SubjectMetadata) -> EstimateResult:
    """Heuristic BF% estimator.

    This MVP uses a hand-tuned linear model on geometric ratios + optional metadata.

    The goal is a *plausible* estimate + wide uncertainty, not clinical accuracy.
    """

    notes: list[str] = []

    feats = compute_features(pose)
    q_pose, q_notes = feature_quality_heuristic(pose)
    notes.extend(q_notes)

    x = feats

    # Base model: tuned to output reasonable ranges for typical adult physiques.
    # Features loosely correlate with adiposity via apparent hip/shoulder widths and trunk proportions.
    bf = 22.0
    bf += 18.0 * (x["hip_to_height_ratio"] - 0.18)
    bf += 10.0 * (x["trunk_to_leg_ratio"] - 0.60)
    bf -= 6.0 * (x["shoulder_to_hip_ratio"] - 1.10)

    # Metadata nudges (very weak)
    if meta.sex == "female":
        bf += 4.0
    elif meta.sex == "male":
        bf -= 2.0
    else:
        notes.append("Sex not provided; uncertainty increased.")

    if meta.age_years is not None:
        bf += 0.05 * (meta.age_years - 30.0)
    else:
        notes.append("Age not provided; uncertainty increased.")

    # BMI-informed correction if height+weight provided
    bmi = None
    if meta.height_cm and meta.weight_kg:
        h_m = meta.height_cm / 100.0
        bmi = meta.weight_kg / (h_m**2)
        # Deurenberg-like weak correction: bf ~ 1.2*bmi + 0.23*age - 10.8*sex - 5.4
        # but blended very lightly to avoid over-reliance on self-reported numbers.
        sex01 = 1.0 if meta.sex == "male" else 0.0
        bf_bmi = 1.2 * bmi + 0.23 * (meta.age_years or 30.0) - 10.8 * sex01 - 5.4
        bf = 0.75 * bf + 0.25 * bf_bmi
    else:
        notes.append("Height/weight not provided; BMI blend skipped.")

    # Clamp to plausible human ranges
    bf = _clamp(bf, 3.0, 60.0)

    # Uncertainty: wide by design.
    width = 10.0
    if meta.sex == "unknown":
        width += 3.0
    if meta.age_years is None:
        width += 2.0
    if bmi is None:
        width += 2.5
    width += (1.0 - q_pose) * 10.0

    low = _clamp(bf - width / 2.0, 2.0, 60.0)
    high = _clamp(bf + width / 2.0, 2.0, 65.0)

    confidence = _clamp(0.25 + 0.55 * q_pose - 0.03 * (width - 10.0), 0.05, 0.85)

    notes.insert(
        0,
        "Prototype estimate based on pose ratios; not validated for clinical use."
        " Use as a rough screening/education aid only.",
    )

    return EstimateResult(
        body_fat_percent=float(bf),
        low_percent=float(low),
        high_percent=float(high),
        confidence=float(confidence),
        notes=notes,
        features={k: float(v) for k, v in feats.items()},
    )
