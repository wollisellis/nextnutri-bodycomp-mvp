from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Sex = Literal["female", "male", "unknown"]


@dataclass(frozen=True)
class SubjectMetadata:
    sex: Sex = "unknown"
    age_years: float | None = None
    height_cm: float | None = None
    weight_kg: float | None = None


@dataclass(frozen=True)
class EstimateResult:
    body_fat_percent: float
    low_percent: float
    high_percent: float
    confidence: float  # 0..1
    notes: list[str]
    features: dict[str, float]
