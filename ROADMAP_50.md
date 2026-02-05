# ROADMAP — 50 etapas (execução autônoma)

Regra do jogo:
- Eu executo em blocos de 10 etapas.
- Ao concluir o bloco, gero um relatório NLP de learnings/artefatos/commits.
- Em seguida, eu mesmo defino o próximo bloco de 10 com base no feedback observado.
- Repito até 50.

## Definição de “pronto” (protótipo)
- Pipeline reprodutível (1 comando) + API com mensagens PT-BR.
- Qualidade aprendida (modelo leve) com rótulos humanos (quando disponível) + fallback por gates.
- Relatórios NLP automáticos + artefatos versionados.
- Worker orientado a milestones (não ficar girando em métricas iguais).

---

## Bloco 1 (Etapas 1–10) — sair do loop e criar fluxo realista

### 1) Criar um “milestone runner” (orquestração) por etapas
- Entregar: `scripts/worker/plan_runner.py` + `reports/plan_state.json`
- Comportamento: executa uma etapa por tick, registra saída, marca concluída, segue.

### 2) Padronizar artefatos e nomes (val vs train)
- Entregar: convenção de nomes e diretórios em `reports/`.
- Remover ambiguidade de `quality_eval.md` sobrescrevendo tudo.

### 3) ROI train completo (não limitado)
- Gerar: `reports/coco_train2017_roi_from_keypoints_pad025.jsonl` (ou pad parametrizado)
- Guardar métricas básicas (n ROIs, distribuição tamanhos).

### 4) Quality eval train (n=5000) com pad=0.25
- Gerar: `reports/quality_eval_train_pad025_n5000.md` (+jsonl ignorado no git)

### 5) Quality eval val (n=5000) com pad=0.25 (baseline)
- Gerar: `reports/quality_eval_val_pad025_n5000.md`

### 6) Relatório NLP “Train vs Val” (pad=0.25)
- Gerar: `reports/delta_train_vs_val_pad025.md`
- Conteúdo: ok/reject, top reasons, recomendações.

### 7) Sweep curto de thresholds (min_side_px / min_area) orientado por taxa de aceitação
- Objetivo: reduzir `too_small` sem aceitar lixo.
- Gerar: `reports/sweep_thresholds_pad025.md`

### 8) Fixar defaults (gates) no código da API
- Atualizar `bodycomp_estimator/quality.py` para refletir thresholds escolhidos.
- Entregar: commit com mudança + nota no report.

### 9) Dataset real rotulado — formato + ferramenta de rotulagem
- Entregar: `data/quality_labeled/README.md` + `scripts/label_quality_cli.py`
- Formato: JSONL com path + label + optional note.

### 10) Modelo aprendido v1 com rótulos humanos (se existirem) e fallback
- Entregar: `bodycomp_estimator/quality_model.py` (load/run) + `reports/quality_model_v1.md`
- Se não houver dados humanos ainda: treinar em proxy e deixar pipeline pronto.

---

## Bloco 2–5
(TBD automaticamente após o Bloco 1.)
