"""Quality gates evaluation on COCO ROI crops.

Goal:
- Create objective, actionable "quality gates" to reject low-quality scans with clear messages.
- Produce a report with counts and suggested thresholds.

Inputs:
- reports/coco_val2017_roi_from_keypoints.jsonl (preferred)
  Each line must include: file (repo-relative or basename), roi_xywh (x,y,w,h)

Outputs:
- reports/quality_eval.jsonl
- reports/quality_eval.md

Run:
  . .venv/bin/activate
  python3 scripts/actions/quality_gates_eval.py --n 1000
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def resolve_img_path(fn: str) -> Path:
    coco_val = REPO / "data" / "datasets" / "coco2017" / "val2017"
    if "/" in fn:
        return (REPO / fn).resolve()
    return coco_val / fn


@dataclass
class Gates:
    min_side_px: int = 160
    min_area_px: int = 160 * 160
    min_brightness: float = 60.0  # mean L channel approx
    max_brightness: float = 215.0
    min_lap_var: float = 80.0  # blur threshold


def brightness_score(bgr: np.ndarray) -> float:
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.float32)
    return float(L.mean())


def blur_score_laplacian(bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def clamp_bbox(xywh, w_img: int, h_img: int):
    x, y, w, h = xywh
    x0 = max(0, int(math.floor(x)))
    y0 = max(0, int(math.floor(y)))
    x1 = min(w_img, int(math.ceil(x + w)))
    y1 = min(h_img, int(math.ceil(y + h)))
    return x0, y0, x1, y1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roi-jsonl", default="reports/coco_val2017_roi_from_keypoints.jsonl")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)

    # Gates (override defaults from code)
    ap.add_argument("--min-side-px", type=int, default=160)
    ap.add_argument("--min-area-px", type=int, default=160 * 160)
    ap.add_argument("--min-brightness", type=float, default=60.0)
    ap.add_argument("--max-brightness", type=float, default=215.0)
    ap.add_argument("--min-lap-var", type=float, default=80.0)

    # Output naming (avoid overwriting when sweeping thresholds)
    ap.add_argument("--out-stem", default="quality_eval", help="Writes reports/<out-stem>.jsonl and .md")

    args = ap.parse_args()

    roi_path = (REPO / args.roi_jsonl).resolve()
    rows = load_jsonl(roi_path)

    random.seed(args.seed)
    sample = random.sample(rows, k=min(args.n, len(rows)))

    gates = Gates(
        min_side_px=int(args.min_side_px),
        min_area_px=int(args.min_area_px),
        min_brightness=float(args.min_brightness),
        max_brightness=float(args.max_brightness),
        min_lap_var=float(args.min_lap_var),
    )

    out_jsonl = REPO / "reports" / f"{args.out_stem}.jsonl"
    out_md = REPO / "reports" / f"{args.out_stem}.md"
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    reasons = Counter()
    status = Counter()

    with out_jsonl.open("w", encoding="utf-8") as f:
        for r in sample:
            # Support multiple ROI list formats produced during development.
            fn = r.get("file") or r.get("file_name")
            roi = r.get("roi_xywh") or r.get("bbox_xywh") or r.get("bbox") or r.get("roi")
            rec = {"file": fn, "roi": roi}

            if not fn or not roi:
                rec["gate"] = "missing_input"
                rec["ok"] = False
                reasons["missing_input"] += 1
                status["reject"] += 1
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue

            img_path = resolve_img_path(fn)
            bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
            if bgr is None:
                rec["gate"] = "read_fail"
                rec["ok"] = False
                reasons["read_fail"] += 1
                status["reject"] += 1
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue

            x0, y0, x1, y1 = clamp_bbox(roi, bgr.shape[1], bgr.shape[0])
            crop = bgr[y0:y1, x0:x1]

            h, w = crop.shape[:2]
            area = int(h * w)
            rec.update({"w": w, "h": h, "area": area})

            if min(w, h) < gates.min_side_px or area < gates.min_area_px:
                rec["gate"] = "too_small"
                rec["ok"] = False
                reasons["too_small"] += 1
                status["reject"] += 1
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue

            b = brightness_score(crop)
            lv = blur_score_laplacian(crop)
            rec.update({"brightness_L_mean": b, "lap_var": lv})

            if b < gates.min_brightness:
                rec["gate"] = "too_dark"
                rec["ok"] = False
                reasons["too_dark"] += 1
                status["reject"] += 1
            elif b > gates.max_brightness:
                rec["gate"] = "too_bright"
                rec["ok"] = False
                reasons["too_bright"] += 1
                status["reject"] += 1
            elif lv < gates.min_lap_var:
                rec["gate"] = "too_blurry"
                rec["ok"] = False
                reasons["too_blurry"] += 1
                status["reject"] += 1
            else:
                rec["gate"] = "ok"
                rec["ok"] = True
                status["ok"] += 1

            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    lines = []
    lines.append("# Quality gates — COCO ROI (sample)\n")
    lines.append(f"Sample: **{len(sample)}**\n")
    lines.append("\n## Current thresholds\n")
    lines.append(f"- min_side_px: {gates.min_side_px}\n")
    lines.append(f"- min_area_px: {gates.min_area_px}\n")
    lines.append(f"- brightness L mean: [{gates.min_brightness}, {gates.max_brightness}]\n")
    lines.append(f"- min_lap_var: {gates.min_lap_var}\n")
    lines.append("\n## Results\n")
    lines.append(f"- ok: **{status['ok']}**\n")
    lines.append(f"- reject: **{status['reject']}**\n")
    lines.append("\n### Reject reasons\n")
    for k, v in reasons.most_common():
        lines.append(f"- {k}: {v}\n")

    lines.append("\n## Suggested user-facing messages (PT-BR)\n")
    lines.append("- too_small: "
                 "A pessoa está pequena no frame. Chegue mais perto e deixe o corpo inteiro visível." "\n")
    lines.append("- too_dark: "
                 "Foto escura. Vire para a luz / aumente iluminação e tente de novo." "\n")
    lines.append("- too_bright: "
                 "Foto estourada (muita luz). Afaste da luz direta e tente de novo." "\n")
    lines.append("- too_blurry: "
                 "Foto tremida/desfocada. Apoie o celular, use temporizador e tente de novo." "\n")

    lines.append("\nArtifacts:\n")
    lines.append(f"- reports/{args.out_stem}.jsonl\n")
    lines.append(f"- reports/{args.out_stem}.md\n")

    out_md.write_text("".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
