# COCO val2017 — Pose: ROI crops vs full image

Rows (ROI bboxes): 213
Unique images: 203

## ROI status counts
- ok: 149
- no_pose: 64

## Full-image status counts (for same images)
- ok: 143
- no_pose: 70

## ROI vs Full (pair counts)
- roi=ok / full=ok: 114
- roi=ok / full=no_pose: 35
- roi=no_pose / full=no_pose: 35
- roi=no_pose / full=ok: 29

## Deltas (interpretation)
- ROI ok & full no_pose: 35
- ROI no_pose & full ok: 29

Artifacts:
- reports/coco_val2017_pose_on_full_from_roi_sample.jsonl
- reports/coco_val2017_pose_roi_vs_full.md
