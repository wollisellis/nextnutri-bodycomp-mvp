"""Milestone-oriented plan runner.

Goal: execute a *finite* ordered plan (10 steps), record outcomes, and avoid
endless metric spinning.

This does NOT replace the existing worker immediately; it's a parallel runner
we can switch the systemd service to once validated.

Artifacts:
- reports/plan_state.json
- reports/plan_actions_log.jsonl

Run:
  . .venv/bin/activate
  python3 scripts/worker/plan_runner.py
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports"
STATE_PATH = REPORTS / "plan_state.json"
ACTIONS_LOG = REPORTS / "plan_actions_log.jsonl"
OUTBOX = REPORTS / "outbox_telegram.txt"


def now_ms() -> int:
    return int(time.time() * 1000)


def write_outbox(mudou: str, rodando: str, proximo: str) -> None:
    OUTBOX.write_text(f"Mudou: {mudou}\nRodando: {rodando}\nPróximo: {proximo}\n", encoding="utf-8")


def append_log(rec: dict) -> None:
    ACTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ACTIONS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"batch": 1, "step": 1, "stepsDone": [], "current": None, "next": None, "updatedAt": None}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(s: dict) -> None:
    s["updatedAt"] = now_ms()
    STATE_PATH.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class Step:
    id: int
    title: str

    def run(self) -> tuple[str, str]:
        """Return (did, next)."""
        raise NotImplementedError


class Step1CreateScaffold(Step):
    def run(self) -> tuple[str, str]:
        REPORTS.mkdir(parents=True, exist_ok=True)
        (REPORTS / "_plan").mkdir(parents=True, exist_ok=True)
        return ("criei scaffold do plan_runner (reports/_plan + logs)", "padronizar nomes de artefatos")


PLAN: list[Step] = [
    Step1CreateScaffold(id=1, title="Create plan runner + plan_state"),
]


def do_one_step() -> None:
    s = load_state()
    step_num = int(s.get("step", 1))

    if step_num > len(PLAN):
        write_outbox("bloco 1 concluído (só scaffold por enquanto)", "idle", "implementar próximas 9 etapas")
        return

    step = PLAN[step_num - 1]

    try:
        did, nxt = step.run()
        s["stepsDone"] = list(s.get("stepsDone", [])) + [step.id]
        s["current"] = step.title
        s["next"] = nxt
        s["step"] = step_num + 1
        save_state(s)

        append_log({"ts": time.time(), "step": step.id, "title": step.title, "ok": True, "did": did, "next": nxt})
        write_outbox(did, "idle", nxt)

    except Exception as e:
        tb = traceback.format_exc()
        append_log({"ts": time.time(), "step": step.id, "title": step.title, "ok": False, "err": str(e), "tb": tb})
        write_outbox(f"erro na etapa {step.id}: {type(e).__name__}", "idle", "ver reports/plan_actions_log.jsonl")


def main() -> int:
    interval_s = 60
    while True:
        do_one_step()
        time.sleep(interval_s)


if __name__ == "__main__":
    raise SystemExit(main())
