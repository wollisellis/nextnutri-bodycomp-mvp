# Learned Quality Model — Baseline (LogReg)

Input: `reports/quality_eval_train_n1000.jsonl`

## What this is
Treinamos um modelo simples (regressão logística) para prever **foto OK vs REJEITAR** usando as mesmas métricas do gate.
Por enquanto, os rótulos vêm das nossas regras (proxy). O objetivo é preparar o pipeline para depois trocar por rótulos humanos.

## Validation metrics (thr=0.5)
- train acc: **0.830**, precision: 1.000, recall: 0.257
- val   acc: **0.835**, precision: 1.000, recall: 0.340

## Strongest signals (by |weight|)
- lap_var: weight=0.816 (↑ OK)
- brightness: weight=0.356 (↑ OK)
- roi_min_side: weight=0.000 (↑ reject)
- roi_area: weight=0.000 (↑ reject)

## Next step
Trocar o target: coletar 200–500 exemplos reais de fotos (clientes) com rótulo humano (ok / motivo).
Aí o modelo passa a aprender *o que importa na prática*, não só reproduzir os gates.

