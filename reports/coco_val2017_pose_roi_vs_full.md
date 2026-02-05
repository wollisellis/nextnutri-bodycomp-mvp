# COCO val2017 — Pose: ROI crops vs full image

Rows (ROI bboxes): 1000
Unique images: 750

## ROI status counts
- ok: 615
- no_pose: 385

## Full-image status counts (for same images)
- ok: 680
- no_pose: 320

## ROI vs Full (pair counts)
- roi=ok / full=ok: 490
- roi=no_pose / full=no_pose: 195
- roi=no_pose / full=ok: 190
- roi=ok / full=no_pose: 125

## Deltas (interpretation)
- ROI ok & full no_pose: 125
- ROI no_pose & full ok: 190

Artifacts:
- reports/coco_val2017_pose_on_full_from_roi_sample.jsonl
- reports/coco_val2017_pose_roi_vs_full.md
