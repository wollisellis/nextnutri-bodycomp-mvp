"""COCO val2017 pose extraction smoke test.

Goal: produce many traceable "actions" (runs) without downloading huge datasets.
This script samples N images from COCO val2017 and attempts MediaPipe pose extraction.

Outputs:
- reports/coco_val_pose_smoketest.jsonl
- reports/coco_val_pose_smoketest_summary.md

Usage:
  . .venv/bin/activate
  python scripts/actions/coco_val_pose_smoketest.py --n 200
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

import cv2

# Allow running as a script without installing the package.
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from bodycomp_estimator.pose import PoseExtractor


def iter_images(val_dir: Path) -> list[Path]:
    return sorted(val_dir.glob("*.jpg"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--val-dir",
        default="data/datasets/coco2017/val2017",
        help="Path to COCO val2017 directory with .jpg files",
    )
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--model-complexity", type=int, default=1)
    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    val_dir = (repo_root / args.val_dir).resolve()
    report_dir = repo_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = report_dir / "coco_val_pose_smoketest.jsonl"
    md_path = report_dir / "coco_val_pose_smoketest_summary.md"

    images = iter_images(val_dir)
    if not images:
        raise SystemExit(f"No images found in {val_dir}")

    random.seed(args.seed)
    sample = random.sample(images, k=min(args.n, len(images)))

    extractor = PoseExtractor(static_image_mode=True, model_complexity=args.model_complexity)

    ok = 0
    no_pose = 0
    errors = 0
    t0 = time.time()

    with jsonl_path.open("w", encoding="utf-8") as f:
        for i, img_path in enumerate(sample, start=1):
            start = time.time()
            rec = {
                "i": i,
                "path": os.path.relpath(img_path, repo_root),
                "ts": time.time(),
            }
            try:
                bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
                if bgr is None:
                    rec["status"] = "read_fail"
                    errors += 1
                else:
                    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                    pose = extractor.extract(rgb)
                    if pose is None:
                        rec["status"] = "no_pose"
                        no_pose += 1
                    else:
                        rec["status"] = "ok"
                        rec["n_landmarks"] = int(pose.xy.shape[0])
                        rec["vis_mean"] = float(pose.visibility.mean()) if pose.visibility is not None else None
                        ok += 1
            except Exception as e:
                rec["status"] = "exception"
                rec["error"] = repr(e)[:400]
                errors += 1
            rec["ms"] = int((time.time() - start) * 1000)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Ensure native resources are released cleanly.
    try:
        extractor.close()
    except Exception:
        pass

    dt = time.time() - t0
    total = len(sample)

    md = []
    md.append("# COCO val2017 — Pose smoketest\n")
    md.append(f"- Images tested: **{total}**\n")
    md.append(f"- OK (pose found): **{ok}**\n")
    md.append(f"- No pose: **{no_pose}**\n")
    md.append(f"- Errors: **{errors}**\n")
    md.append(f"- Total time: **{dt:.1f}s** (avg **{dt/total:.3f}s/img**)\n")
    md.append("\nArtifacts:\n")
    md.append(f"- `{jsonl_path.relative_to(repo_root)}`\n")
    md.append(f"- `{md_path.relative_to(repo_root)}`\n")

    md_path.write_text("".join(md), encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
