# Artifact conventions

We avoid overwriting ambiguous files. Prefer explicit, comparable stems:

- coco_<split>2017_roi_from_keypoints_pad{pad}.jsonl
- quality_eval_<split>_pad{pad}_n{n}.md
- delta_train_vs_val_pad{pad}.md

Notes:
- Large JSONL outputs are kept locally and ignored by git.
