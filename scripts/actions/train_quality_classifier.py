"""Train a simple *learned* quality classifier from existing gate outputs.

This is step 1 towards "A: foto boa vs foto ruim".

Important caveat:
- This trains on labels produced by our current heuristics/gates.
- It is NOT ground truth, but it lets us learn a smoother decision boundary,
  quantify feature importance, and later swap labels to human labels.

Inputs:
- reports/quality_eval_train_n1000.jsonl (or any quality_eval*.jsonl)
  Each record has: gate (or status), brightness_L_mean, lap_var, min_side_px, area_px, etc.

Outputs:
- reports/quality_model_baseline.json (weights + thresholds)
- reports/quality_model_baseline.md (NLP summary)

We intentionally avoid heavy ML deps (sklearn). Uses a tiny logistic regression
trainer implemented with numpy.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


@dataclass
class Dataset:
    X: np.ndarray
    y: np.ndarray
    feat_names: list[str]


def build_dataset(rows: list[dict]) -> Dataset:
    """Binary label: 1=ok, 0=reject (any gate)."""

    # Features we expect from quality_gates_eval.py
    # If missing, fill with nan then impute.
    feat_names = [
        "brightness",
        "lap_var",
        "roi_min_side",
        "roi_area",
    ]

    X_list = []
    y_list = []

    for r in rows:
        # Our evaluator writes boolean `ok` plus a `gate` string.
        # `gate` is usually one of: ok, too_small, too_dark, too_bright, too_blurry.
        ok_flag = r.get("ok")
        gate = r.get("gate")

        if ok_flag is True or gate == "ok":
            ok = 1
        else:
            ok = 0

        # The evaluator stores computed metrics under these keys (we add them later if missing).
        b = r.get("brightness") or r.get("brightness_L_mean")
        lv = r.get("lap_var") or r.get("laplacian_var")
        ms = r.get("roi_min_side") or r.get("min_side_px")
        area = r.get("roi_area") or r.get("area_px")

        X_list.append([
            float("nan") if b is None else float(b),
            float("nan") if lv is None else float(lv),
            float("nan") if ms is None else float(ms),
            float("nan") if area is None else float(area),
        ])
        y_list.append(ok)

    X = np.asarray(X_list, dtype=np.float32)
    y = np.asarray(y_list, dtype=np.float32)

    # Simple imputation: replace nan with column median
    for j in range(X.shape[1]):
        col = X[:, j]
        mask = np.isfinite(col)
        if not mask.any():
            X[:, j] = 0.0
        else:
            med = np.median(col[mask])
            col[~mask] = med
            X[:, j] = col

    # Standardize
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma = np.where(sigma < 1e-6, 1.0, sigma)
    Xz = (X - mu) / sigma

    return Dataset(X=Xz, y=y, feat_names=feat_names), mu, sigma


def train_logreg(X: np.ndarray, y: np.ndarray, lr: float = 0.2, steps: int = 4000, l2: float = 0.01):
    n, d = X.shape
    w = np.zeros((d,), dtype=np.float32)
    b = 0.0

    for _ in range(steps):
        z = X @ w + b
        p = sigmoid(z)
        # gradients
        gw = (X.T @ (p - y)) / n + l2 * w
        gb = float((p - y).mean())
        w -= lr * gw
        b -= lr * gb

    return w, float(b)


def metrics(p: np.ndarray, y: np.ndarray, thr: float = 0.5) -> dict:
    pred = (p >= thr).astype(np.float32)
    acc = float((pred == y).mean())
    tp = float(((pred == 1) & (y == 1)).sum())
    tn = float(((pred == 0) & (y == 0)).sum())
    fp = float(((pred == 1) & (y == 0)).sum())
    fn = float(((pred == 0) & (y == 1)).sum())
    prec = tp / max(1.0, (tp + fp))
    rec = tp / max(1.0, (tp + fn))
    return {
        "acc": acc,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": prec,
        "recall": rec,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default="reports/quality_eval_train_n1000.jsonl")
    ap.add_argument("--out-stem", default="quality_model_baseline")
    args = ap.parse_args()

    p = (REPO / args.jsonl).resolve()
    rows = load_jsonl(p)

    (ds, mu, sigma) = build_dataset(rows)
    X, y = ds.X, ds.y

    # Train/val split
    rng = np.random.default_rng(42)
    idx = np.arange(len(y))
    rng.shuffle(idx)
    cut = int(0.8 * len(idx))
    tr, va = idx[:cut], idx[cut:]

    w, b = train_logreg(X[tr], y[tr])

    p_tr = sigmoid(X[tr] @ w + b)
    p_va = sigmoid(X[va] @ w + b)

    m_tr = metrics(p_tr, y[tr])
    m_va = metrics(p_va, y[va])

    out_json = REPO / "reports" / f"{args.out_stem}.json"
    out_md = REPO / "reports" / f"{args.out_stem}.md"

    payload = {
        "ts": time.time(),
        "input": str(Path(args.jsonl)),
        "features": ds.feat_names,
        "standardize_mu": mu.tolist(),
        "standardize_sigma": sigma.tolist(),
        "weights": w.tolist(),
        "bias": b,
        "train_metrics": m_tr,
        "val_metrics": m_va,
        "note": "Trained on heuristic gate labels (proxy). Replace with human labels later.",
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Human/NLP summary
    def fmt(x: float) -> str:
        return f"{x:.3f}"

    w_pairs = list(zip(ds.feat_names, w.tolist()))
    w_pairs.sort(key=lambda t: abs(t[1]), reverse=True)

    lines = []
    lines.append("# Learned Quality Model — Baseline (LogReg)")
    lines.append("")
    lines.append(f"Input: `{Path(args.jsonl)}`")
    lines.append("")
    lines.append("## What this is")
    lines.append(
        "Treinamos um modelo simples (regressão logística) para prever **foto OK vs REJEITAR** usando as mesmas métricas do gate.\n"
        "Por enquanto, os rótulos vêm das nossas regras (proxy). O objetivo é preparar o pipeline para depois trocar por rótulos humanos."  # noqa: E501
    )
    lines.append("")
    lines.append("## Validation metrics (thr=0.5)")
    lines.append(f"- train acc: **{fmt(m_tr['acc'])}**, precision: {fmt(m_tr['precision'])}, recall: {fmt(m_tr['recall'])}")
    lines.append(f"- val   acc: **{fmt(m_va['acc'])}**, precision: {fmt(m_va['precision'])}, recall: {fmt(m_va['recall'])}")
    lines.append("")
    lines.append("## Strongest signals (by |weight|)")
    for name, ww in w_pairs:
        direction = "↑ OK" if ww > 0 else "↑ reject"
        lines.append(f"- {name}: weight={fmt(float(ww))} ({direction})")
    lines.append("")
    lines.append("## Next step")
    lines.append(
        "Trocar o target: coletar 200–500 exemplos reais de fotos (clientes) com rótulo humano (ok / motivo).\n"
        "Aí o modelo passa a aprender *o que importa na prática*, não só reproduzir os gates."  # noqa: E501
    )
    lines.append("")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
