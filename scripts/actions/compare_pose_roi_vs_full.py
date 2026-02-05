"""Compare pose extraction success on ROI crops vs full images.

Inputs:
- reports/coco_val2017_pose_on_roi_sample.jsonl (records: file,bbox,status)

Outputs:
- reports/coco_val2017_pose_roi_vs_full.md
- reports/coco_val2017_pose_on_full_from_roi_sample.jsonl

Run:
  . .venv/bin/activate
  python3 scripts/actions/compare_pose_roi_vs_full.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2

REPO = Path(__file__).resolve().parents[2]

# Allow running as a script without installing the package.
import sys

sys.path.insert(0, str(REPO))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def resolve_img_path(fn: str) -> Path:
    coco_val = REPO / "data" / "datasets" / "coco2017" / "val2017"
    if "/" in fn:
        return (REPO / fn).resolve()
    return coco_val / fn


def main() -> int:
    from bodycomp_estimator.pose import PoseExtractor

    roi_jsonl = REPO / "reports" / "coco_val2017_pose_on_roi_sample.jsonl"
    if not roi_jsonl.exists():
        raise SystemExit(f"missing input: {roi_jsonl}")

    rows = load_jsonl(roi_jsonl)
    # Keep order; compare per-row. Some files can repeat with different bboxes.

    extractor = PoseExtractor(static_image_mode=True)

    out_full_jsonl = REPO / "reports" / "coco_val2017_pose_on_full_from_roi_sample.jsonl"
    out_md = REPO / "reports" / "coco_val2017_pose_roi_vs_full.md"

    status_pairs = Counter()
    full_status_counts = Counter()

    # Cache full-image inference by file to reduce repeats.
    full_cache: dict[str, str] = {}

    with out_full_jsonl.open("w", encoding="utf-8") as f:
        for r in rows:
            fn = r.get("file")
            roi_status = r.get("status")
            if not fn:
                full_status = "missing_file_name"
            else:
                if fn in full_cache:
                    full_status = full_cache[fn]
                else:
                    img_path = resolve_img_path(fn)
                    bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
                    if bgr is None:
                        full_status = "read_fail"
                    else:
                        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                        pose = extractor.extract(rgb)
                        full_status = "ok" if pose is not None else "no_pose"
                    full_cache[fn] = full_status

            status_pairs[(roi_status, full_status)] += 1
            full_status_counts[full_status] += 1

            rec = {
                "file": fn,
                "roi_status": roi_status,
                "full_status": full_status,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    try:
        extractor.close()
    except Exception:
        pass

    # Summaries
    roi_counts = Counter(r.get("status") for r in rows)
    n = len(rows)

    lines = []
    lines.append("# COCO val2017 — Pose: ROI crops vs full image")
    lines.append("")
    lines.append(f"Rows (ROI bboxes): {n}")
    lines.append(f"Unique images: {len(full_cache)}")
    lines.append("")
    lines.append("## ROI status counts")
    for k, v in roi_counts.most_common():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Full-image status counts (for same images)")
    for k, v in full_status_counts.most_common():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## ROI vs Full (pair counts)")
    for (roi_s, full_s), v in status_pairs.most_common():
        lines.append(f"- roi={roi_s} / full={full_s}: {v}")

    # Key comparisons
    roi_ok_full_no = status_pairs.get(("ok", "no_pose"), 0)
    roi_no_full_ok = status_pairs.get(("no_pose", "ok"), 0)
    lines.append("")
    lines.append("## Deltas (interpretation)")
    lines.append(f"- ROI ok & full no_pose: {roi_ok_full_no}")
    lines.append(f"- ROI no_pose & full ok: {roi_no_full_ok}")
    lines.append("")
    lines.append("Artifacts:")
    lines.append(f"- {out_full_jsonl.relative_to(REPO)}")
    lines.append(f"- {out_md.relative_to(REPO)}")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
