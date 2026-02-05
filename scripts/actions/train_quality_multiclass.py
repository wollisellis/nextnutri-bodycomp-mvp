"""Train a tiny multi-class quality model from human labels.

Labels:
- ok, too_dark, too_bright, too_blurry, too_small

Input:
- data/quality_labeled/labels.jsonl
  {"file": "images/xxx.jpg", "label": "ok|too_dark|...", "note": "..."}

Output:
- data/quality_labeled/model/quality_multiclass.json   (LOCAL ONLY)
- reports/quality_model_multiclass.md                  (NLP summary)

Notes:
- No heavy deps (no sklearn). Uses numpy + simple softmax regression.
- If no labels exist, writes a report saying it's waiting for data.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]

CLASSES = ["ok", "too_dark", "too_bright", "too_blurry", "too_small"]
C2I = {c: i for i, c in enumerate(CLASSES)}


def load_labels(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    return rows


def load_image_rgb(path: Path) -> np.ndarray:
    # Use cv2 if available; else fail.
    import cv2

    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(str(path))
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb


def gray(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)
    return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)


def brightness(rgb: np.ndarray) -> float:
    return float(gray(rgb).mean())


def lap_var(rgb: np.ndarray) -> float:
    g = gray(rgb)
    c = g
    lap = -4.0 * c + np.roll(c, 1, 0) + np.roll(c, -1, 0) + np.roll(c, 1, 1) + np.roll(c, -1, 1)
    return float(lap.var())


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def train_softmax(X: np.ndarray, y: np.ndarray, lr: float = 0.3, steps: int = 3000, l2: float = 0.01):
    n, d = X.shape
    k = int(y.max()) + 1
    W = np.zeros((d, k), dtype=np.float32)
    b = np.zeros((k,), dtype=np.float32)

    Y = np.eye(k, dtype=np.float32)[y]

    for _ in range(steps):
        logits = X @ W + b
        P = softmax(logits)
        # grad
        G = (P - Y) / n
        gW = X.T @ G + l2 * W
        gb = G.sum(axis=0)
        W -= lr * gW
        b -= lr * gb

    return W, b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="data/quality_labeled/labels.jsonl")
    ap.add_argument("--out-model", default="data/quality_labeled/model/quality_multiclass.json")
    ap.add_argument("--out-md", default="reports/quality_model_multiclass.md")
    ap.add_argument("--max", type=int, default=5000)
    args = ap.parse_args()

    labels_path = (REPO / args.labels).resolve()
    rows = load_labels(labels_path)

    out_md = (REPO / args.out_md).resolve()
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        out_md.write_text(
            "# Quality model (multi-class)\n\n"
            "Status: aguardando labels humanos em `data/quality_labeled/labels.jsonl`.\n",
            encoding="utf-8",
        )
        print(str(out_md))
        return 0

    rows = rows[: args.max]

    X_list = []
    y_list = []
    cnt = Counter()

    for r in rows:
        label = r.get("label")
        if label not in C2I:
            continue
        rel = r.get("file")
        if not isinstance(rel, str):
            continue
        img_path = (REPO / "data" / "quality_labeled" / rel).resolve() if not rel.startswith("data/") else (REPO / rel).resolve()
        rgb = load_image_rgb(img_path)

        X_list.append([brightness(rgb), lap_var(rgb), float(rgb.shape[1]), float(rgb.shape[0])])
        y_list.append(C2I[label])
        cnt[label] += 1

    X = np.asarray(X_list, dtype=np.float32)
    y = np.asarray(y_list, dtype=np.int64)

    # standardize
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma = np.where(sigma < 1e-6, 1.0, sigma)
    Xz = (X - mu) / sigma

    # split
    rng = np.random.default_rng(42)
    idx = np.arange(len(y))
    rng.shuffle(idx)
    cut = int(0.8 * len(idx))
    tr, va = idx[:cut], idx[cut:]

    W, b = train_softmax(Xz[tr], y[tr])

    def acc(ii):
        P = softmax(Xz[ii] @ W + b)
        pred = P.argmax(axis=1)
        return float((pred == y[ii]).mean())

    acc_tr = acc(tr)
    acc_va = acc(va) if len(va) else float("nan")

    model_path = (REPO / args.out_model).resolve()
    model_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "ts": time.time(),
        "classes": CLASSES,
        "features": ["brightness", "lap_var", "width", "height"],
        "standardize_mu": mu.tolist(),
        "standardize_sigma": sigma.tolist(),
        "W": W.tolist(),
        "b": b.tolist(),
        "train_acc": acc_tr,
        "val_acc": acc_va,
        "label_counts": dict(cnt),
        "note": "Local-only. Replace/extend features as needed.",
    }
    model_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out_md.write_text(
        "# Quality model (multi-class)\n\n"
        f"Exemplos usados: **{len(y)}**\n\n"
        f"Train acc: **{acc_tr:.3f}**\n"
        f"Val acc: **{acc_va:.3f}**\n\n"
        "Contagem por classe:\n"
        + "\n".join([f"- {k}: {v}" for k, v in cnt.most_common()])
        + "\n\n"
        f"Modelo salvo em (local): `{model_path.relative_to(REPO)}`\n",
        encoding="utf-8",
    )

    print(str(out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
