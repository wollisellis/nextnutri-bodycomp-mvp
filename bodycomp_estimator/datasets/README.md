# Datasets & calibration notes

This repo intentionally **does not ship** any datasets.

Body composition estimation from photos is a sensitive topic. Before using any dataset:

- verify consent, license, and allowed uses
- avoid datasets with nudity/explicit imagery unless you have strong governance
- consider ethics review and data minimization

## Potentially useful open datasets

### 1) BodyM (silhouettes + body measurements)
- Source: https://registry.opendata.aws/bodym/
- What it contains: **frontal + side silhouettes** (binary) and 14 body measurements, height, weight, gender.
- License: CC BY-NC 4.0 (non-commercial).
- Why it helps: can be used to learn a mapping from **shape/silhouette features** → **circumferences**, which can then be related to body fat via separate label sources.

⚠️ Note: while these are silhouettes (not raw photos), this is still human-shape data; treat as sensitive.

### 2) NHANES (DEXA body composition + anthropometrics; no images)
- Source portal: https://wwwn.cdc.gov/nchs/nhanes/Default.aspx
- Contains: rich anthropometrics and (for certain cycles) DXA body composition measures.
- Why it helps: can be used to calibrate a regression from anthropometrics (BMI, waist, etc.) → body fat %, then later connect image-derived measurements to those anthropometrics.

### 3) Pose/keypoint datasets (for pose robustness; not body fat labels)
- COCO Keypoints: https://cocodataset.org/
- MPII Human Pose: http://human-pose.mpi-inf.mpg.de/

These datasets improve pose estimation and invariance to camera/pose, but **do not** provide body-fat ground truth.

## Brazil-specific calibration roadmap

A practical route for Brazil population calibration (without collecting sensitive imagery early):

1. **Phase A (no images):** build & validate a strong baseline BF% model using Brazilian/LatAm references if available (e.g., DXA/BIA studies + anthropometrics). Output uncertainty by sex/age group.
2. **Phase B (controlled pilot images):** collect a small, consented dataset in clinics/gyms with standardized protocol (distance, lens, clothing guidelines), and a reference method (DXA preferred; otherwise multi-frequency BIA with documented device).
3. **Phase C (domain adaptation):** fit a calibration layer (e.g., isotonic regression / linear recalibration) that maps MVP photo-estimates to the Brazilian reference.

## Download placeholders

See `scripts/datasets/` for **non-downloading** placeholders that describe how to obtain data.
