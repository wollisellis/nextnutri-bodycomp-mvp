# Plano autônomo — Bloco 1 (Etapas 1–10)

Objetivo: parar de “girar métricas” e evoluir para um fluxo de construção com milestones.

## Etapas 1–10 (o que vai sair na prática)
1. Orquestração por etapas (plan runner + estado persistente)
2. Padronização de artefatos (nomes e não sobrescrever relatórios)
3. ROI train completo (pad=0.25)
4. Quality eval train n=5000 (pad=0.25)
5. Quality eval val n=5000 (pad=0.25)
6. Relatório NLP: delta train vs val
7. Sweep de thresholds guiado por aceitação (reduzir too_small)
8. Fixar defaults na API (quality.py)
9. Ferramenta e formato de rotulagem humana (JSONL + CLI)
10. Modelo aprendido v1 de qualidade + fallback

## Estado atual
- Worker legacy (runner.py) ainda está rodando (systemd).
- Já temos: COCO train+val no disco; quality eval train n=1000; status_summary.md.
- Gap: worker precisa alternar train/val e gerar deltas automáticos.

## Entregáveis por bloco
- 1–3 relatórios NLP (md) por bloco.
- Commits/pushes marcados por milestone.
