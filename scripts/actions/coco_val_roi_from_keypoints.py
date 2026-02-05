"""COCO val2017 ROI from person keypoints annotations.

Purpose
- Build a reproducible ROI (crop box) per COCO person instance using the
  `person_keypoints_val2017.json` annotations.
- This ROI can be used to re-run pose extraction on a tighter crop and compare
  results vs full-frame.

Outputs
- reports/coco_val2017_roi_from_keypoints.jsonl

Each record is one person annotation with:
- image_id, ann_id
- file_name (relative)
- roi_xywh (float)
- kp_xy_minmax (float)
- n_kp_visible

Usage
  . .venv/bin/activate
  python scripts/actions/coco_val_roi_from_keypoints.py \
    --ann data/datasets/coco2017/annotations/person_keypoints_val2017.json \
    --images-dir data/datasets/coco2017/val2017 \
    --pad-frac 0.15
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def _xywh_from_kps(keypoints: list[float], pad_frac: float) -> tuple[float, float, float, float] | None:
    """Return ROI xywh from COCO keypoints list (len=51), using v>0 points."""
    if not keypoints or len(keypoints) % 3 != 0:
        return None

    xs: list[float] = []
    ys: list[float] = []
    for i in range(0, len(keypoints), 3):
        x, y, v = keypoints[i], keypoints[i + 1], keypoints[i + 2]
        if v and v > 0:
            xs.append(float(x))
            ys.append(float(y))

    if not xs:
        return None

    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    w = max(1.0, x1 - x0)
    h = max(1.0, y1 - y0)

    pad_x = w * pad_frac
    pad_y = h * pad_frac

    rx0 = x0 - pad_x
    ry0 = y0 - pad_y
    rw = w + 2 * pad_x
    rh = h + 2 * pad_y
    return rx0, ry0, rw, rh


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--ann",
        default="data/datasets/coco2017/annotations/person_keypoints_val2017.json",
        help="Path to COCO person_keypoints_val2017.json",
    )
    p.add_argument(
        "--images-dir",
        default="data/datasets/coco2017/val2017",
        help="Directory containing val2017 .jpg files (for relative paths)",
    )
    p.add_argument("--pad-frac", type=float, default=0.15)
    p.add_argument("--limit", type=int, default=0, help="If >0, limit number of annotations processed")
    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    ann_path = (repo_root / args.ann).resolve()
    images_dir = (repo_root / args.images_dir).resolve()
    report_dir = repo_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    out_path = report_dir / "coco_val2017_roi_from_keypoints.jsonl"

    data: dict[str, Any] = json.loads(ann_path.read_text(encoding="utf-8"))
    images = {int(img["id"]): img for img in data.get("images", [])}
    anns = data.get("annotations", [])

    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for ann in anns:
            if args.limit and n >= args.limit:
                break

            if int(ann.get("category_id", 0)) != 1:
                continue  # person

            image_id = int(ann["image_id"])
            img = images.get(image_id)
            if not img:
                continue

            roi = _xywh_from_kps(ann.get("keypoints", []), pad_frac=float(args.pad_frac))
            if roi is None:
                continue

            # Count visible keypoints
            kps = ann.get("keypoints", [])
            n_vis = 0
            for i in range(0, len(kps), 3):
                v = kps[i + 2]
                if v and v > 0:
                    n_vis += 1

            file_name = str(img.get("file_name"))
            rel_img = os.path.relpath(images_dir / file_name, repo_root)

            rec = {
                "image_id": image_id,
                "ann_id": int(ann["id"]),
                "file": rel_img,
                "roi_xywh": [float(x) for x in roi],
                "kp_xy_minmax": None,  # reserved for future detail
                "n_kp_visible": int(n_vis),
                "area": float(ann.get("area")) if ann.get("area") is not None else None,
                "bbox_xywh": [float(x) for x in ann.get("bbox", [])] if ann.get("bbox") is not None else None,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1

    print(f"Wrote {n} ROI records to {out_path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
