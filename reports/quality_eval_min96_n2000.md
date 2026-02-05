# Quality gates — COCO ROI (sample)
Sample: **2000**

## Current thresholds
- min_side_px: 96
- min_area_px: 9216
- brightness L mean: [60.0, 215.0]
- min_lap_var: 80.0

## Results
- ok: **841**
- reject: **1159**

### Reject reasons
- too_small: 1086
- too_dark: 69
- too_blurry: 4

## Suggested user-facing messages (PT-BR)
- too_small: A pessoa está pequena no frame. Chegue mais perto e deixe o corpo inteiro visível.
- too_dark: Foto escura. Vire para a luz / aumente iluminação e tente de novo.
- too_bright: Foto estourada (muita luz). Afaste da luz direta e tente de novo.
- too_blurry: Foto tremida/desfocada. Apoie o celular, use temporizador e tente de novo.

Artifacts:
- reports/quality_eval_min96_n2000.jsonl
- reports/quality_eval_min96_n2000.md
