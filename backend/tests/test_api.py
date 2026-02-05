from __future__ import annotations

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _make_test_image() -> bytes:
    # Simple RGB image; pose extractor will be monkeypatched.
    img = Image.fromarray(np.zeros((64, 64, 3), dtype=np.uint8), mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_estimate_happy_path_monkeypatched_pose(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from bodycomp_estimator.pose import PoseLandmarks

    # Minimal plausible landmarks array for required indices.
    xy = np.zeros((33, 2), dtype=np.float32)
    # Nose, shoulders, hips, ankles
    xy[0] = [0.5, 0.1]
    xy[11] = [0.4, 0.3]
    xy[12] = [0.6, 0.3]
    xy[23] = [0.45, 0.55]
    xy[24] = [0.55, 0.55]
    xy[27] = [0.47, 0.95]
    xy[28] = [0.53, 0.95]
    vis = np.ones((33,), dtype=np.float32)

    def fake_extract(_img_rgb: np.ndarray):
        return PoseLandmarks(xy=xy, visibility=vis)

    # Patch the global extractor in the app module
    import backend.app.main as main

    monkeypatch.setattr(main.pose_extractor, "extract", fake_extract)

    img_bytes = _make_test_image()
    r = client.post(
        "/estimate",
        files={"image": ("test.png", img_bytes, "image/png")},
        data={"sex": "female", "age_years": 30, "height_cm": 165, "weight_kg": 65},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert 2.0 <= data["range"]["low"] <= data["body_fat_percent"] <= data["range"]["high"]
    assert 0.0 <= data["confidence"] <= 1.0
    assert "disclaimer" in data


def test_estimate_invalid_sex(client: TestClient) -> None:
    img_bytes = _make_test_image()
    r = client.post(
        "/estimate",
        files={"image": ("test.png", img_bytes, "image/png")},
        data={"sex": "other"},
    )
    assert r.status_code in (400, 422)
