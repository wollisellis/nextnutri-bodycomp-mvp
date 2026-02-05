from __future__ import annotations

import io

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from bodycomp_estimator.estimator import estimate_body_fat_percent
from bodycomp_estimator.pose import PoseExtractor
from bodycomp_estimator.schemas import SubjectMetadata
from bodycomp_estimator.quality import quality_gate_message

app = FastAPI(title="NextNutri BodyComp MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

pose_extractor = PoseExtractor(static_image_mode=True, model_complexity=1)


def _quality_payload(ok: bool, reason: str, message_ptbr: str) -> dict:
    return {
        "quality_ok": ok,
        "quality_reason": reason,
        "quality_message_ptbr": message_ptbr,
    }


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

    # Fast quality gates before pose (blur/light).
    msg = quality_gate_message(image_rgb)
    if msg is not None:
        # structured detail for clients
        raise HTTPException(status_code=422, detail=_quality_payload(False, 'precheck', msg))

    pose = pose_extractor.extract(image_rgb)
    if pose is None:
        raise HTTPException(
            status_code=422,
            detail=_quality_payload(
                False,
                'no_pose',
                ("Não detectei pose. Use uma foto de corpo inteiro (cabeça aos pés), "
                 "bem iluminada, em pé, sem oclusões (braços colados no corpo ajudam)."),
            ),
        )

    # Post-pose gate: person too small in frame.
    msg2 = quality_gate_message(image_rgb, pose_xy_norm=pose.xy)
    if msg2 is not None:
        raise HTTPException(status_code=422, detail=_quality_payload(False, 'too_small', msg2))

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
