#!/usr/bin/env python3
# CLI simples para rotular qualidade.
#
# Uso:
#   python3 scripts/label_quality_cli.py data/quality_labeled/images
#
# Atalhos:
#   o=ok, d=too_dark, b=too_bright, l=too_blurry, s=too_small, q=sair

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "quality_labeled" / "labels.jsonl"
MAP = {"o": "ok", "d": "too_dark", "b": "too_bright", "l": "too_blurry", "s": "too_small"}


def main() -> int:
    img_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else (ROOT / "data" / "quality_labeled" / "images")
    img_dir.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    imgs = sorted(img_dir.glob("*.jpg"))
    if not imgs:
        print("No .jpg files in", img_dir)
        return 1

    print("Labeling", len(imgs), "images in", img_dir)
    print("Keys: o/d/b/l/s, q to quit")

    for p in imgs:
        print("
FILE:", p.name)
        k = input("label> ").strip().lower()
        if k == "q":
            break
        if k not in MAP:
            print("skip")
            continue

        rec = {"file": str(p.relative_to(ROOT / "data" / "quality_labeled")), "label": MAP[k]}
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "
")
        print("saved:", rec)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
