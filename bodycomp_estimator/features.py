from __future__ import annotations

import math

import numpy as np

from .pose import PoseLandmarks


# MediaPipe Pose landmark indices
# https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _mid(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a + b) / 2.0


def compute_features(pose: PoseLandmarks) -> dict[str, float]:
    """Compute simple, scale-invariant ratios from 2D pose.

    Important limitations:
      - These ratios are *not* direct circumferences.
      - Clothing, camera angle, and body pose can introduce large errors.
    """

    xy = pose.xy

    ls, rs = xy[LEFT_SHOULDER], xy[RIGHT_SHOULDER]
    lh, rh = xy[LEFT_HIP], xy[RIGHT_HIP]
    la, ra = xy[LEFT_ANKLE], xy[RIGHT_ANKLE]
    nose = xy[NOSE]

    shoulder_w = _dist(ls, rs)
    hip_w = _dist(lh, rh)
    trunk_len = _dist(_mid(ls, rs), _mid(lh, rh))
    leg_len = _dist(_mid(lh, rh), _mid(la, ra))
    approx_height = _dist(nose, _mid(la, ra))

    eps = 1e-6

    return {
        "shoulder_to_hip_ratio": shoulder_w / (hip_w + eps),
        "trunk_to_leg_ratio": trunk_len / (leg_len + eps),
        "hip_to_height_ratio": hip_w / (approx_height + eps),
        "shoulder_to_height_ratio": shoulder_w / (approx_height + eps),
        "trunk_to_height_ratio": trunk_len / (approx_height + eps),
        "approx_height_norm": approx_height,  # already normalized (0..~1.5)
        "pose_ok": 1.0,
    }


def feature_quality_heuristic(pose: PoseLandmarks) -> tuple[float, list[str]]:
    """Return (quality 0..1, notes)."""

    notes: list[str] = []
    if pose.visibility is None:
        return 0.6, ["No landmark visibility provided; quality degraded."]

    # Require that key landmarks are reasonably visible
    key_ids = [LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP, LEFT_ANKLE, RIGHT_ANKLE]
    key_vis = float(np.mean([pose.visibility[i] for i in key_ids]))

    q = max(0.0, min(1.0, key_vis))
    if q < 0.5:
        notes.append("Low landmark visibility; ensure full-body photo with good lighting.")

    # Penalize extreme aspect ratios (likely cropped)
    feats = compute_features(pose)
    h = feats["approx_height_norm"]
    if h < 0.45:
        notes.append("Subject appears cropped; include full body head-to-feet.")
        q *= 0.6

    return q, notes
