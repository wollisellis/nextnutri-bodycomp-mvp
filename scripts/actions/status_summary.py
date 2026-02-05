"""Generate a consolidated, human-readable (NLP-style) status report.

Goal: one artifact you can open to understand the current state quickly.

Writes: reports/status_summary.md
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports"


def sh(cmd: list[str]) -> str:
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        return ""
    return r.stdout.strip()


def newest(path_glob: str) -> Path | None:
    cands = sorted(REPORTS.glob(path_glob), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def read_last_jsonl(p: Path, n: int = 15) -> list[dict]:
    if not p.exists():
        return []
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out = []
    for ln in lines[-n:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)

    git_sha = sh(["git", "rev-parse", "--short", "HEAD"]) or "unknown"
    git_branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"

    # Dataset counts (if present)
    coco_root = REPO / "data" / "datasets" / "coco2017"
    train_dir = coco_root / "train2017"
    val_dir = coco_root / "val2017"
    train_n = len(list(train_dir.glob("*.jpg"))) if train_dir.exists() else 0
    val_n = len(list(val_dir.glob("*.jpg"))) if val_dir.exists() else 0

    # Disk snapshot
    df_line = sh(["bash", "-lc", "df -h / | tail -n 1"]) or ""

    # Worker state
    worker_state_path = REPORTS / "worker_state.json"
    worker_state = {}
    if worker_state_path.exists():
        try:
            worker_state = json.loads(worker_state_path.read_text(encoding="utf-8"))
        except Exception:
            worker_state = {}

    # Recent actions
    actions = read_last_jsonl(REPORTS / "actions_log.jsonl", n=12)

    # Newest eval artifacts
    newest_quality_md = newest("quality_eval*.md")
    newest_quality_jsonl = None
    if newest_quality_md:
        stem = newest_quality_md.name.replace(".md", "")
        cand = REPORTS / f"{stem}.jsonl"
        if cand.exists():
            newest_quality_jsonl = cand

    # Optional: other known reports
    compare_roi_full = REPORTS / "coco_val2017_pose_roi_vs_full.md"

    # Build report
    now_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    lines: list[str] = []
    lines.append("# Status Summary — NextNutri BodyComp MVP")
    lines.append("")
    lines.append(f"Gerado em: **{now_utc}**")
    lines.append(f"Git: **{git_branch} @ {git_sha}**")
    lines.append("")

    lines.append("## Dataset (COCO 2017)")
    lines.append(f"- train2017: **{train_n:,}** imagens".replace(",", "."))
    lines.append(f"- val2017: **{val_n:,}** imagens".replace(",", "."))
    lines.append("")

    lines.append("## Infra / Disco")
    if df_line:
        lines.append(f"- `df -h /`: `{df_line}`")
    else:
        lines.append("- `df -h /`: (indisponível)")
    lines.append("")

    lines.append("## Worker (estado)")
    if worker_state:
        lines.append(f"- tick: **{worker_state.get('tick')}**")
        lines.append(f"- última ação: **{worker_state.get('lastAction')}**")
        lines.append(f"- próxima ação: **{worker_state.get('nextAction')}**")
    else:
        lines.append("- (sem worker_state.json)")
    lines.append("")

    lines.append("## Últimas ações (log)")
    if actions:
        for a in actions[::-1]:
            ok = "ok" if a.get("ok", True) else "erro"
            tick = a.get("tick")
            act = a.get("action")
            nxt = a.get("next")
            lines.append(f"- tick {tick} [{ok}]: {act} → próximo: {nxt}")
    else:
        lines.append("- (sem actions_log.jsonl)")
    lines.append("")

    lines.append("## Artefatos recentes")
    if newest_quality_md:
        lines.append(f"- Quality gates (mais recente): `{newest_quality_md.relative_to(REPO)}`")
    if newest_quality_jsonl:
        lines.append(f"- Quality gates (dados): `{newest_quality_jsonl.relative_to(REPO)}`")
    if compare_roi_full.exists():
        lines.append(f"- ROI vs Full (val): `{compare_roi_full.relative_to(REPO)}`")
    lines.append("")

    lines.append("## Leitura humana (o que isso significa)")
    lines.append(
        "- A gente já tem **COCO train+val** localmente, então dá pra parar de 'smoke test' e começar a medir estabilidade com amostras maiores.\n"
        "- O worker está rodando num ciclo simples (ROI list ↔ pose em ROI ↔ quality gates).\n"
        "- Próximo upgrade é: **rodar os mesmos relatórios em train2017** (não só val) e comparar deltas (train vs val)."
    )
    lines.append("")

    out = REPORTS / "status_summary.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
