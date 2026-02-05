from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class QualityGates:
    """Simple, fast quality gates.

    These gates are intentionally conservative: if we reject, we provide an actionable message.
    They are NOT a guarantee of correctness.
    """

    # Full-image gates
    min_brightness_L_mean: float = 55.0
    max_brightness_L_mean: float = 225.0
    min_lap_var: float = 60.0

    # Pose-relative gates (computed after pose detection)
    min_pose_bbox_area_ratio: float = 0.08  # person must occupy >=8% of image
    min_pose_bbox_min_side_ratio: float = 0.35  # bbox min side >=35% of image min side


def _to_gray(image_rgb: np.ndarray) -> np.ndarray:
    r = image_rgb[:, :, 0].astype(np.float32)
    g = image_rgb[:, :, 1].astype(np.float32)
    b = image_rgb[:, :, 2].astype(np.float32)
    return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)


def laplacian_var(image_rgb: np.ndarray) -> float:
    """Variance of a discrete Laplacian (blur proxy). No OpenCV dependency."""
    gray = _to_gray(image_rgb)
    # 2D Laplacian kernel (4-neighborhood)
    #   0  1  0
    #   1 -4  1
    #   0  1  0
    c = gray
    lap = (
        -4.0 * c
        + np.roll(c, 1, axis=0)
        + np.roll(c, -1, axis=0)
        + np.roll(c, 1, axis=1)
        + np.roll(c, -1, axis=1)
    )
    return float(lap.var())


def brightness_L_mean(image_rgb: np.ndarray) -> float:
    """Approx brightness. Uses mean of grayscale as proxy for L channel."""
    gray = _to_gray(image_rgb)
    return float(gray.mean())


def pose_bbox_from_landmarks_xy(pose_xy_norm: np.ndarray) -> tuple[float, float, float, float]:
    """Return normalized bbox (xmin, ymin, xmax, ymax) from normalized landmark xy."""
    xs = pose_xy_norm[:, 0]
    ys = pose_xy_norm[:, 1]
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())


def quality_gate_message(
    image_rgb: np.ndarray,
    pose_xy_norm: np.ndarray | None = None,
    gates: QualityGates | None = None,
) -> str | None:
    """Return a PT-BR rejection message if quality is insufficient, else None."""

    g = gates or QualityGates()

    b = brightness_L_mean(image_rgb)
    if b < g.min_brightness_L_mean:
        return "Foto escura. Vire para a luz / aumente a iluminação e tente de novo."
    if b > g.max_brightness_L_mean:
        return "Foto estourada (muita luz). Afaste da luz direta e tente de novo."

    lv = laplacian_var(image_rgb)
    if lv < g.min_lap_var:
        return "Foto tremida/desfocada. Apoie o celular, use temporizador e tente de novo."

    if pose_xy_norm is not None:
        h, w = image_rgb.shape[:2]
        xmin, ymin, xmax, ymax = pose_bbox_from_landmarks_xy(pose_xy_norm)
        # Clamp to [0,1] defensively
        xmin = max(0.0, min(1.0, xmin))
        xmax = max(0.0, min(1.0, xmax))
        ymin = max(0.0, min(1.0, ymin))
        ymax = max(0.0, min(1.0, ymax))

        bw = max(0.0, xmax - xmin)
        bh = max(0.0, ymax - ymin)
        area_ratio = bw * bh
        min_side_ratio = min(bw * w, bh * h) / max(1.0, min(w, h))

        if area_ratio < g.min_pose_bbox_area_ratio or min_side_ratio < g.min_pose_bbox_min_side_ratio:
            return (
                "A pessoa está pequena no frame. Chegue mais perto e deixe o corpo inteiro visível (cabeça aos pés)."
            )

    return None
