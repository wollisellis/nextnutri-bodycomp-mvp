from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class PoseLandmarks:
    """Normalized 2D landmarks in image coordinates [0..1]."""

    xy: np.ndarray  # (N, 2)
    visibility: np.ndarray | None = None  # (N,)


class PoseExtractor:
    """MediaPipe Pose wrapper.

    We support the modern MediaPipe Tasks API (mediapipe>=0.10.3x).

    Notes:
        - MediaPipe returns *normalized* landmark coordinates.
        - For a photo-based body comp MVP, we only compute geometric ratios.
        - This is NOT a medical device and should not be used for diagnosis.
    """

    DEFAULT_MODEL_URL = (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    )

    def __init__(
        self,
        static_image_mode: bool = True,
        model_complexity: int = 1,
        model_path: str | None = None,
    ):
        # `model_complexity` kept for compatibility; Tasks model choice is via model file.
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity

        self.model_path = Path(model_path) if model_path else self._default_model_path()
        self._landmarker = None

    def _default_model_path(self) -> Path:
        # repo-local cache (works in API + scripts)
        return Path("data/models/mediapipe/pose_landmarker_lite.task")

    def _ensure_model(self) -> None:
        if self.model_path.exists():
            return
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        # Tiny download (~6–10MB). We keep it explicit and fail with a clear error.
        try:
            import urllib.request

            urllib.request.urlretrieve(self.DEFAULT_MODEL_URL, self.model_path)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Could not download MediaPipe pose landmarker model. "
                f"Tried: {self.DEFAULT_MODEL_URL} -> {self.model_path}"
            ) from e

    def _get_landmarker(self):
        if self._landmarker is not None:
            return self._landmarker

        try:
            # Use explicit module paths to avoid import quirks across mediapipe builds.
            from mediapipe.tasks.python.core.base_options import BaseOptions
            from mediapipe.tasks.python import vision
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "mediapipe (Tasks API) is required for pose extraction. Install requirements.txt"
            ) from e

        self._ensure_model()

        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        return self._landmarker

    def close(self) -> None:
        if self._landmarker is not None:
            try:
                self._landmarker.close()
            except Exception:
                pass
            self._landmarker = None

    def __del__(self):  # pragma: no cover
        # Avoid noisy interpreter-shutdown errors.
        try:
            self.close()
        except Exception:
            pass

    def extract(self, image_rgb: np.ndarray) -> PoseLandmarks | None:
        from mediapipe import Image, ImageFormat

        landmarker = self._get_landmarker()

        mp_image = Image(image_format=ImageFormat.SRGB, data=image_rgb)
        result = landmarker.detect(mp_image)

        if not result.pose_landmarks:
            return None

        # Use the first detected pose.
        lms = result.pose_landmarks[0]
        xy = np.array([[lm.x, lm.y] for lm in lms], dtype=np.float32)

        # Some models expose visibility; if missing, keep None.
        vis = None
        try:
            vis = np.array([getattr(lm, "visibility", 0.0) for lm in lms], dtype=np.float32)
        except Exception:
            vis = None

        return PoseLandmarks(xy=xy, visibility=vis)
