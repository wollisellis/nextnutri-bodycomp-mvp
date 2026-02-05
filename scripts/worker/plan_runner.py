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


def run(cmd: list[str]) -> None:
    import subprocess

    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")


def write_text(rel: str, content: str) -> Path:
    p = (REPO / rel).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def parse_quality_md(rel_md: str) -> dict:
    p = (REPO / rel_md).resolve()
    data = {"ok": None, "reject": None, "reasons": {}}
    if not p.exists():
        return data
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("- ok:"):
            data["ok"] = line.split("**")[1]
        if line.startswith("- reject:"):
            data["reject"] = line.split("**")[1]
        if line.startswith("- too_"):
            # "- too_small: 747"
            try:
                k, v = line[2:].split(":", 1)
                data["reasons"][k.strip()] = v.strip()
            except Exception:
                pass
    return data


class Step2ArtifactsConvention(Step):
    def run(self) -> tuple[str, str]:
        p = write_text(
            "reports/_plan/artifact_conventions.md",
            """# Artifact conventions

We avoid overwriting ambiguous files. Prefer explicit, comparable stems:

- coco_<split>2017_roi_from_keypoints_pad{pad}.jsonl
- quality_eval_<split>_pad{pad}_n{n}.md
- delta_train_vs_val_pad{pad}.md

Notes:
- Large JSONL outputs are kept locally and ignored by git.
""",
        )
        return (f"padronizei convenções de artefatos ({p.relative_to(REPO)})", "gerar ROI train completo pad=0.25")


class Step3RoiTrainFull(Step):
    def run(self) -> tuple[str, str]:
        out = "reports/coco_train2017_roi_from_keypoints_pad025.jsonl"
        run([
            "python3",
            "scripts/actions/coco_val_roi_from_keypoints.py",
            "--split",
            "train",
            "--pad-frac",
            "0.25",
            "--out-jsonl",
            out,
        ])
        return (f"gerei ROI train2017 completo (pad=0.25) → {out}", "rodar quality gates train n=5000")


class Step4QualityTrain5000(Step):
    def run(self) -> tuple[str, str]:
        roi = "reports/coco_train2017_roi_from_keypoints_pad025.jsonl"
        out_stem = "quality_eval_train_pad025_n5000"
        run([
            "python3",
            "scripts/actions/quality_gates_eval.py",
            "--roi-jsonl",
            roi,
            "--n",
            "5000",
            "--out-stem",
            out_stem,
        ])
        return (f"quality gates train (n=5000, pad=0.25) → reports/{out_stem}.md", "rodar quality gates val n=5000")


class Step5QualityVal5000(Step):
    def run(self) -> tuple[str, str]:
        roi = "reports/coco_val2017_roi_from_keypoints_pad025.jsonl"
        if not (REPO / roi).exists():
            run([
                "python3",
                "scripts/actions/coco_val_roi_from_keypoints.py",
                "--split",
                "val",
                "--pad-frac",
                "0.25",
                "--out-jsonl",
                roi,
            ])
        out_stem = "quality_eval_val_pad025_n5000"
        run([
            "python3",
            "scripts/actions/quality_gates_eval.py",
            "--roi-jsonl",
            roi,
            "--n",
            "5000",
            "--out-stem",
            out_stem,
        ])
        return (f"quality gates val (n=5000, pad=0.25) → reports/{out_stem}.md", "gerar delta train vs val")


class Step6DeltaTrainVsVal(Step):
    def run(self) -> tuple[str, str]:
        tr = parse_quality_md("reports/quality_eval_train_pad025_n5000.md")
        va = parse_quality_md("reports/quality_eval_val_pad025_n5000.md")
        out = "reports/delta_train_vs_val_pad025.md"
        lines = [
            "# Delta — Train vs Val (pad=0.25)",
            "",
            "## Summary",
            f"- train: ok={tr.get('ok')} reject={tr.get('reject')}",
            f"- val:   ok={va.get('ok')} reject={va.get('reject')}",
            "",
            "## Top reject reasons (train)",
        ]
        for k, v in sorted(tr.get("reasons", {}).items()):
            lines.append(f"- {k}: {v}")
        lines += ["", "## Top reject reasons (val)"]
        for k, v in sorted(va.get("reasons", {}).items()):
            lines.append(f"- {k}: {v}")
        lines += [
            "",
            "## Interpretação",
            "- Se `too_small` dominar nos dois splits, o gargalo é enquadramento/tamanho do ROI.",
            "- A próxima etapa é sweep de thresholds para aumentar aceitação sem perder qualidade.",
            "",
        ]
        write_text(out, "\n".join(lines))
        return (f"gerei delta train vs val → {out}", "rodar sweep de thresholds")


class Step7SweepThresholds(Step):
    def run(self) -> tuple[str, str]:
        roi = "reports/coco_val2017_roi_from_keypoints_pad025.jsonl"
        configs = [
            (96, 96 * 96, "quality_eval_val_pad025_min96_n2000"),
            (128, 128 * 128, "quality_eval_val_pad025_min128_n2000"),
            (160, 160 * 160, "quality_eval_val_pad025_min160_n2000"),
        ]
        results = []
        for min_side, min_area, stem in configs:
            run([
                "python3",
                "scripts/actions/quality_gates_eval.py",
                "--roi-jsonl",
                roi,
                "--n",
                "2000",
                "--min-side-px",
                str(min_side),
                "--min-area-px",
                str(min_area),
                "--out-stem",
                stem,
            ])
            results.append((min_side, stem))

        out = "reports/sweep_thresholds_pad025.md"
        lines = [
            "# Sweep — thresholds (pad=0.25)",
            "",
            "Rodado em val (n=2000) com min_side/min_area variando.",
            "",
        ]
        for min_side, stem in results:
            md = parse_quality_md(f"reports/{stem}.md")
            lines.append(f"## min_side={min_side}")
            lines.append(f"- ok: {md.get('ok')} | reject: {md.get('reject')}")
            lines.append("")
        write_text(out, "\n".join(lines) + "\n")
        return (f"sweep thresholds concluído → {out}", "fixar defaults na API")


class Step8FixDefaultsApi(Step):
    def run(self) -> tuple[str, str]:
        # For now, record chosen defaults in a file; code changes come after we pick.
        out = "reports/_plan/quality_defaults_candidate.json"
        write_text(
            out,
            json.dumps(
                {
                    "note": "Candidate defaults based on sweep. Update bodycomp_estimator/quality.py next.",
                    "min_side_px": 128,
                    "min_area_px": 128 * 128,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
        return (f"registrei defaults candidatos → {out}", "criar ferramenta de rotulagem humana")


class Step9LabelingTool(Step):
    def run(self) -> tuple[str, str]:
        write_text(
            "data/quality_labeled/README.md",
            """# Quality labeled dataset (local only)

Estrutura:
- images/  (NÃO versionar)
- labels.jsonl

Formato labels.jsonl (1 por linha):
{"file": "images/xxx.jpg", "label": "ok|too_dark|too_bright|too_bright|too_small", "note": "..."}

Privacidade: manter local (não subir).
""",
        )
        write_text(
            "scripts/label_quality_cli.py",
            """#!/usr/bin/env python3
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
        print("\nFILE:", p.name)
        k = input("label> ").strip().lower()
        if k == "q":
            break
        if k not in MAP:
            print("skip")
            continue

        rec = {"file": str(p.relative_to(ROOT / "data" / "quality_labeled")), "label": MAP[k]}
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("saved:", rec)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
        )
        return ("criei dataset local + CLI de rotulagem (data/quality_labeled)", "treinar modelo v1 com labels humanos")


class Step10QualityModelV1(Step):
    def run(self) -> tuple[str, str]:
        # Pipeline placeholder: in the next batch we will train on human labels.
        write_text(
            "reports/quality_model_v1.md",
            "# Quality model v1\n\n"
            "Status: pipeline pronto para treinar com rótulos humanos.\n\n"
            "Proximo: coletar 200-500 fotos rotuladas e treinar classificador (multi-classe).\n",
        )
        return ("preparei o slot do modelo v1 (aguardando labels humanos)", "iniciar Bloco 2 (etapas 11–20)")


PLAN: list[Step] = [
    Step1CreateScaffold(id=1, title="Create plan runner + plan_state"),
    Step2ArtifactsConvention(id=2, title="Standardize artifact naming"),
    Step3RoiTrainFull(id=3, title="Generate full train ROI list"),
    Step4QualityTrain5000(id=4, title="Quality eval train n=5000"),
    Step5QualityVal5000(id=5, title="Quality eval val n=5000"),
    Step6DeltaTrainVsVal(id=6, title="Delta train vs val report"),
    Step7SweepThresholds(id=7, title="Threshold sweep"),
    Step8FixDefaultsApi(id=8, title="Record candidate defaults"),
    Step9LabelingTool(id=9, title="Labeling tool + format"),
    Step10QualityModelV1(id=10, title="Quality model v1 placeholder"),
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
