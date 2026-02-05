# COCO val2017 — Pose: ROI crops vs full image

Rows (ROI bboxes): 1000
Unique images: 750

## ROI status counts
- ok: 653
- no_pose: 347

## Full-image status counts (for same images)
- ok: 680
- no_pose: 320

## ROI vs Full (pair counts)
- roi=ok / full=ok: 507
- roi=no_pose / full=no_pose: 174
- roi=no_pose / full=ok: 173
- roi=ok / full=no_pose: 146

## Deltas (interpretation)
- ROI ok & full no_pose: 146
- ROI no_pose & full ok: 173

Artifacts:
- reports/coco_val2017_pose_on_full_from_roi_sample.jsonl
- reports/coco_val2017_pose_roi_vs_full.md
