"""Autonomous local runner (continuous loop).

Design goals:
- Do NOT depend on OpenClaw cron RPC for each step.
- Persist continuity in reports/worker_state.json.
- Emit a 3-line Telegram update to reports/outbox_telegram.txt after each action.
  A separate OpenClaw cron job can send that outbox via the `message` tool.

Run (systemd service recommended):
  . .venv/bin/activate
  python3 scripts/worker/runner.py
"""

from __future__ import annotations

import json
import os
import random
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
# Ensure repo root is importable (bodycomp_estimator, etc.).
sys.path.insert(0, str(REPO))

STATE_PATH = REPO / "reports" / "worker_state.json"
OUTBOX_PATH = REPO / "reports" / "outbox_telegram.txt"
ERROR_PATH = REPO / "reports" / "worker_last_error.txt"
ACTIONS_LOG_PATH = REPO / "reports" / "actions_log.jsonl"


@dataclass
class State:
    tick: int
    last_action: str | None
    next_action: str
    last_tick_at_ms: int | None = None


def now_ms() -> int:
    return int(time.time() * 1000)


def load_state() -> State:
    if not STATE_PATH.exists():
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        s = State(tick=0, last_action=None, next_action="ROI crop COCO keypoints", last_tick_at_ms=None)
        save_state(s)
        return s
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return State(
        tick=int(data.get("tick", 0)),
        last_action=data.get("lastAction"),
        next_action=str(data.get("nextAction", "ROI crop COCO keypoints")),
        last_tick_at_ms=data.get("lastTickAtMs"),
    )


def save_state(s: State) -> None:
    payload = {
        "tick": s.tick,
        "lastAction": s.last_action,
        "nextAction": s.next_action,
        "lastTickAtMs": s.last_tick_at_ms,
    }
    STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_outbox(mudou: str, rodando: str, proximo: str) -> None:
    OUTBOX_PATH.write_text(f"Mudou: {mudou}\nRodando: {rodando}\nPróximo: {proximo}\n", encoding="utf-8")


def append_action_log(tick: int, action: str, next_action: str, ok: bool, extra: dict | None = None) -> None:
    rec = {
        "ts": time.time(),
        "tick": tick,
        "ok": ok,
        "action": action,
        "next": next_action,
    }
    if extra:
        rec.update(extra)
    ACTIONS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ACTIONS_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def action_roi_list_from_keypoints(pad_frac: float = 0.15) -> tuple[str, str]:
    """(summary, next_action)

    Uses the dedicated script so ROI format stays consistent.
    """
    import subprocess

    cmd = [
        "python3",
        "scripts/actions/coco_val_roi_from_keypoints.py",
        "--pad-frac",
        str(pad_frac),
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        return (f"erro ao gerar ROI (pad={pad_frac})", "investigar coco_val_roi_from_keypoints.py")

    return (
        f"gerei ROIs via keypoints (pad={pad_frac})",
        "rodar pose em ROI sample 1000 e comparar vs full",
    )


def action_quality_gates(n: int = 1000) -> tuple[str, str]:
    import subprocess

    cmd = ["python3", "scripts/actions/quality_gates_eval.py", "--n", str(n)]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        return ("erro em quality gates", "ver logs/traceback")

    # Parse report headline quickly
    md = (REPO / "reports" / "quality_eval.md").read_text(encoding="utf-8")
    ok_line = next((l for l in md.splitlines() if l.startswith("- ok:")), "- ok: ?")
    rej_line = next((l for l in md.splitlines() if l.startswith("- reject:")), "- reject: ?")
    return (f"quality gates {ok_line} {rej_line}", "ajustar ROI pad e rerodar quality gates")


def action_rerun_pose_on_roi_sample(n: int = 200, seed: int = 42) -> tuple[str, str]:
    import cv2

    from bodycomp_estimator.pose import PoseExtractor

    roi_list = REPO / "reports" / "coco_val2017_roi_from_keypoints.jsonl"
    img_dir = REPO / "data" / "datasets" / "coco2017" / "val2017"
    out_jsonl = REPO / "reports" / "coco_val2017_pose_on_roi_sample.jsonl"
    out_md = REPO / "reports" / "coco_val2017_pose_on_roi_sample_summary.md"

    if not roi_list.exists():
        return ("faltou ROI list; não rodei pose", "gerar ROI list")

    rows = [json.loads(line) for line in roi_list.read_text(encoding="utf-8").splitlines() if line.strip()]
    random.seed(seed)
    sample = random.sample(rows, k=min(n, len(rows)))

    extractor = PoseExtractor(static_image_mode=True)

    ok = 0
    no_pose = 0
    read_fail = 0

    with out_jsonl.open("w", encoding="utf-8") as f:
        for r in sample:
            fn = r.get("file_name") or r.get("file") or ""
            bbox = r.get("bbox") or r.get("roi_xywh") or r.get("bbox_xywh")
            rec = {"file": fn or None, "bbox": bbox}

            if not isinstance(fn, str) or not fn.strip():
                rec["status"] = "missing_file_name"
                read_fail += 1
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue
            fn = fn.strip()

            if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
                rec["status"] = "missing_or_invalid_bbox"
                read_fail += 1
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue

            # `fn` may be a bare COCO file_name (0000.jpg) or a repo-relative path.
            if "/" in fn:
                img_path = (REPO / fn).resolve()
            else:
                img_path = img_dir / fn

            bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
            if bgr is None:
                rec["status"] = "read_fail"
                read_fail += 1
            else:
                x, y, w, h = bbox
                x0 = max(0, int(x))
                y0 = max(0, int(y))
                x1 = min(bgr.shape[1], int(x + w))
                y1 = min(bgr.shape[0], int(y + h))
                crop = bgr[y0:y1, x0:x1]
                if crop.size == 0:
                    rec["status"] = "empty_crop"
                    read_fail += 1
                else:
                    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                    pose = extractor.extract(rgb)
                    if pose is None:
                        rec["status"] = "no_pose"
                        no_pose += 1
                    else:
                        rec["status"] = "ok"
                        ok += 1

            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    try:
        extractor.close()
    except Exception:
        pass

    out_md.write_text(
        "\n".join(
            [
                "# COCO val2017 — Pose on ROI sample",
                f"- Sample: {len(sample)}",
                f"- OK: {ok}",
                f"- No pose: {no_pose}",
                f"- Read/crop fail: {read_fail}",
                "",
                "Artifacts:",
                f"- {out_jsonl.relative_to(REPO)}",
                f"- {out_md.relative_to(REPO)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return (f"rodei pose em ROI sample {len(sample)} (ok={ok}, no_pose={no_pose})", "aumentar sample p/ 1000 + quality gates")


def maybe_milestone_commit(tick: int) -> None:
    """Every N ticks, try to create a lightweight milestone commit + push.

    Best-effort: never crash the worker.
    """

    if tick % 25 != 0:
        return

    try:
        import subprocess

        subprocess.run(
            ["git", "add", "backend", "bodycomp_estimator", "scripts", "reports", ".gitignore"],
            cwd=str(REPO),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Only commit if there is something staged/changed.
        r = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=str(REPO),
            check=False,
        )
        if r.returncode == 0:
            return

        subprocess.run(
            ["git", "commit", "-m", f"Milestone: worker tick {tick}"],
            cwd=str(REPO),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "push"],
            cwd=str(REPO),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return


def do_one_action(s: State) -> State:
    s.tick += 1
    s.last_tick_at_ms = now_ms()

    # Simple autonomous scheduler (no user input):
    # - every 5 ticks: regenerate ROI list (alternate pad)
    # - every 2 ticks: alternate pose eval and quality gates
    if s.tick % 5 == 0:
        pad = 0.15 if (s.tick // 5) % 2 == 0 else 0.25
        summary, nxt = action_roi_list_from_keypoints(pad_frac=pad)
    elif s.tick % 2 == 0:
        summary, nxt = action_quality_gates(n=1000)
    else:
        summary, nxt = action_rerun_pose_on_roi_sample(n=1000)

    s.last_action = summary
    s.next_action = nxt
    save_state(s)

    append_action_log(tick=s.tick, action=summary, next_action=nxt, ok=True)
    maybe_milestone_commit(s.tick)

    write_outbox(
        mudou=summary,
        rodando="idle",
        proximo=nxt,
    )
    return s


def main() -> int:
    interval_s = int(os.environ.get("WORKER_INTERVAL_S", "60"))
    while True:
        try:
            s = load_state()
            do_one_action(s)
        except Exception as e:
            # Never crash loop; report error in outbox + persist traceback.
            tb = traceback.format_exc()
            try:
                ERROR_PATH.write_text(tb, encoding="utf-8")
            except Exception:
                pass
            append_action_log(
                tick=load_state().tick,
                action=f"erro: {type(e).__name__}",
                next_action="investigar traceback",
                ok=False,
            )
            write_outbox(
                mudou=f"erro: {type(e).__name__}",
                rodando="idle",
                proximo="ver reports/worker_last_error.txt",
            )
        time.sleep(interval_s)


if __name__ == "__main__":
    raise SystemExit(main())
