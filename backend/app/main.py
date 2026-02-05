from __future__ import annotations

import io

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from bodycomp_estimator.estimator import estimate_body_fat_percent
from bodycomp_estimator.pose import PoseExtractor
from bodycomp_estimator.schemas import SubjectMetadata

app = FastAPI(title="NextNutri BodyComp MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

pose_extractor = PoseExtractor(static_image_mode=True, model_complexity=1)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/estimate")
async def estimate(
    image: UploadFile = File(..., description="Front-facing full-body photo"),
    sex: str = Form("unknown"),
    age_years: float | None = Form(None),
    height_cm: float | None = Form(None),
    weight_kg: float | None = Form(None),
) -> dict:
    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload")

    try:
        pil = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}") from e

    image_rgb = np.array(pil)

    pose = pose_extractor.extract(image_rgb)
    if pose is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "No pose detected. Use a clear, well-lit full-body photo (head-to-feet), "
                "standing upright, minimal occlusion."
            ),
        )

    sex_norm = sex.lower().strip()
    if sex_norm not in {"female", "male", "unknown"}:
        raise HTTPException(status_code=400, detail="sex must be female|male|unknown")

    meta = SubjectMetadata(
        sex=sex_norm, age_years=age_years, height_cm=height_cm, weight_kg=weight_kg
    )
    result = estimate_body_fat_percent(pose, meta)

    return {
        "body_fat_percent": result.body_fat_percent,
        "range": {"low": result.low_percent, "high": result.high_percent},
        "confidence": result.confidence,
        "notes": result.notes,
        "features": result.features,
        "disclaimer": (
            "This is a research/prototype estimate with high uncertainty; not medical advice. "
            "Do not use for diagnosis or treatment decisions."
        ),
    }
