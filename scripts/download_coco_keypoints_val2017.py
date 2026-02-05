"""Download COCO 2017 annotations and extract person_keypoints_val2017.json.

Why: ROI crop pipeline depends on person_keypoints_val2017.json.

Usage:
  cd /home/unienutri/.openclaw/workspace/nextnutri-bodycomp-mvp && . .venv/bin/activate
  python3 scripts/download_coco_keypoints_val2017.py
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import sys
import time
import urllib.request
import zipfile


COCO_ANN_ZIP_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
TARGET_MEMBER = "annotations/person_keypoints_val2017.json"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, out_path: pathlib.Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    # If partial exists, try resume.
    resume_from = tmp_path.stat().st_size if tmp_path.exists() else 0
    req = urllib.request.Request(url)
    if resume_from > 0:
        req.add_header("Range", f"bytes={resume_from}-")

    with urllib.request.urlopen(req) as resp:
        # If server ignored Range, start over.
        if resume_from > 0 and getattr(resp, "status", None) == 200:
            resume_from = 0
            tmp_path.unlink(missing_ok=True)

        total = resp.headers.get("Content-Length")
        total = int(total) + resume_from if total is not None else None

        mode = "ab" if resume_from > 0 else "wb"
        downloaded = resume_from
        t0 = time.time()
        last_print = 0.0

        with tmp_path.open(mode) as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_print > 1.0:
                    last_print = now
                    if total:
                        pct = 100.0 * downloaded / total
                        speed = downloaded / max(now - t0, 1e-6) / (1024 * 1024)
                        print(f"download: {pct:5.1f}% ({downloaded/1e6:.1f}MB/{total/1e6:.1f}MB) {speed:.1f} MB/s", flush=True)
                    else:
                        print(f"download: {downloaded/1e6:.1f}MB", flush=True)

    tmp_path.replace(out_path)


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data" / "coco"
    zip_path = data_dir / "annotations_trainval2017.zip"
    out_path = data_dir / "annotations" / "person_keypoints_val2017.json"

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"OK: already exists: {out_path} ({out_path.stat().st_size/1e6:.1f}MB)")
        return 0

    print(f"Downloading COCO annotations zip -> {zip_path}")
    download(COCO_ANN_ZIP_URL, zip_path)
    print(f"Download complete: {zip_path} ({zip_path.stat().st_size/1e6:.1f}MB)")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        members = set(z.namelist())
        if TARGET_MEMBER not in members:
            print(f"ERROR: member not found in zip: {TARGET_MEMBER}")
            print("Members under annotations/:", [m for m in z.namelist() if m.startswith('annotations/')][:50])
            return 2
        print(f"Extracting {TARGET_MEMBER} -> {out_path}")
        with z.open(TARGET_MEMBER) as src, out_path.open("wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)

    print(f"OK: extracted: {out_path} ({out_path.stat().st_size/1e6:.1f}MB)")
    print(f"sha256: {sha256_file(out_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
