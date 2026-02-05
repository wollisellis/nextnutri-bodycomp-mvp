# NextNutri BodyComp MVP (photo-based body fat % prototype)

**Audience:** nutrition professionals who want a *rough*, photo-based body composition estimate to support education and screening.

## Disclaimer (read first)

- This project is a **research / prototype**.
- Outputs are **probabilistic estimates with high uncertainty**.
- **Not a medical device.** Do **not** use for diagnosis, treatment decisions, or claims.
- Photo conditions (pose, clothing, camera angle, lens distortion, lighting) can dominate the estimate.

## What this MVP does

- **FastAPI backend**: `POST /estimate` accepts an image + optional metadata.
- **MediaPipe Pose** extraction.
- **Feature engineering**: simple 2D geometric ratios (scale-invariant).
- **Heuristic estimator**: hand-tuned linear blend + conservative uncertainty range.
- **Streamlit demo UI** to upload an image and view an estimate.

## Repo name suggestion

Suggested GitHub repo name under `wollisellis`:

- `nextnutri-bodycomp-mvp`

(Alternatives: `bodycomp-photo-mvp`, `nextnutri-bodycomp-estimator`.)

## Quickstart

### 1) Backend (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

uvicorn backend.app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### 2) Streamlit demo

```bash
pip install -r requirements-streamlit.txt
streamlit run streamlit_app/app.py
```

Point the UI at `http://localhost:8000`.

## API

### `POST /estimate`

Multipart form fields:
- `image` (file): full-body image
- `sex`: `female|male|unknown`
- `age_years`: float (optional)
- `height_cm`: float (optional)
- `weight_kg`: float (optional)

Response:
- `body_fat_percent`
- `range.low`, `range.high`
- `confidence` (0..1)
- `notes`

## Calibration roadmap (Brazil)

See: `bodycomp_estimator/datasets/README.md`

High-level steps:
1. Build a baseline using open anthropometric + DXA/BIA label sources (no images).
2. Run a small consented Brazilian pilot with standardized photos + reference method.
3. Fit a calibration layer (recalibration + uncertainty).

## Development

### Lint

```bash
ruff check .
ruff format .
```

### Tests

```bash
pytest
```

## Limitations (non-exhaustive)

- Works best only on **front-facing**, **standing**, **full-body** images.
- Not robust to sitting poses, extreme camera angles, heavy occlusion.
- No segmentation / circumference estimation in this MVP.
- Not validated on Brazilian population (yet).
