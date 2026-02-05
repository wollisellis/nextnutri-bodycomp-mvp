from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PoseLandmarks:
    """Normalized 2D landmarks in image coordinates [0..1]."""

    xy: np.ndarray  # (N, 2)
    visibility: np.ndarray | None = None  # (N,)


class PoseExtractor:
    """MediaPipe Pose wrapper.

    Notes:
        - MediaPipe returns *normalized* landmark coordinates.
        - For a photo-based body comp MVP, we only compute geometric ratios.
        - This is NOT a medical device and should not be used for diagnosis.
    """

    def __init__(self, static_image_mode: bool = True, model_complexity: int = 1):
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity

    def extract(self, image_rgb: np.ndarray) -> PoseLandmarks | None:
        try:
            import mediapipe as mp
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "mediapipe is required for pose extraction. Install requirements.txt"
            ) from e

        mp_pose = mp.solutions.pose

        with mp_pose.Pose(
            static_image_mode=self.static_image_mode,
            model_complexity=self.model_complexity,
            enable_segmentation=False,
        ) as pose:
            results = pose.process(image_rgb)

        if not results.pose_landmarks:
            return None

        lms = results.pose_landmarks.landmark
        xy = np.array([[lm.x, lm.y] for lm in lms], dtype=np.float32)
        vis = np.array([lm.visibility for lm in lms], dtype=np.float32)
        return PoseLandmarks(xy=xy, visibility=vis)
