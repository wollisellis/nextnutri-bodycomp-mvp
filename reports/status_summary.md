# Status Summary — NextNutri BodyComp MVP

Gerado em: **2026-02-05 16:50:28 UTC**
Git: **main @ 2062aa7**

## Dataset (COCO 2017)
- train2017: **118.287** imagens
- val2017: **5.000** imagens

## Infra / Disco
- `df -h /`: `/dev/sda1        99G   33G   62G  35% /`

## Worker (estado)
- tick: **315**
- última ação: **gerei ROIs via keypoints (pad=0.25)**
- próxima ação: **aumentar amostra ROI→full (n≈1000) e regenerar relatório comparativo**

## Últimas ações (log)
- tick 315 [ok]: gerei ROIs via keypoints (pad=0.25) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 314 [ok]: quality gates - ok: **210** - reject: **790** → próximo: ajustar ROI pad e rerodar quality gates
- tick 313 [ok]: rodei pose em ROI sample 1000 (ok=615, no_pose=385) → próximo: aumentar sample p/ 1000 + quality gates
- tick 312 [ok]: quality gates - ok: **210** - reject: **790** → próximo: ajustar ROI pad e rerodar quality gates
- tick 311 [ok]: rodei pose em ROI sample 1000 (ok=615, no_pose=385) → próximo: aumentar sample p/ 1000 + quality gates
- tick 310 [ok]: gerei ROIs via keypoints (pad=0.15) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 309 [ok]: rodei pose em ROI sample 1000 (ok=653, no_pose=347) → próximo: aumentar sample p/ 1000 + quality gates
- tick 308 [ok]: quality gates - ok: **247** - reject: **753** → próximo: ajustar ROI pad e rerodar quality gates
- tick 307 [ok]: rodei pose em ROI sample 1000 (ok=653, no_pose=347) → próximo: aumentar sample p/ 1000 + quality gates
- tick 306 [ok]: quality gates - ok: **247** - reject: **753** → próximo: ajustar ROI pad e rerodar quality gates
- tick 305 [ok]: gerei ROIs via keypoints (pad=0.25) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 304 [ok]: quality gates - ok: **210** - reject: **790** → próximo: ajustar ROI pad e rerodar quality gates

## Artefatos recentes
- Quality gates (mais recente): `reports/quality_eval_val_pad025_min160_n2000.md`
- Quality gates (dados): `reports/quality_eval_val_pad025_min160_n2000.jsonl`
- Quality gates (train n=1000): `reports/quality_eval_train_n1000.md`
- Quality gates (val n=1000): `reports/quality_eval_n1000.md`
- ROI vs Full (val): `reports/coco_val2017_pose_roi_vs_full.md`

## Leitura humana (o que isso significa)
- A gente já tem **COCO train+val** localmente, então dá pra parar de 'smoke test' e começar a medir estabilidade com amostras maiores.
- O worker está rodando num ciclo simples (ROI list ↔ pose em ROI ↔ quality gates).
- ROI vs Full (val, amostra pequena): **roi ok/full no_pose = 35** e **roi no_pose/full ok = 29** (ver `reports/coco_val2017_pose_roi_vs_full.md`).
- Próximo upgrade é: **rodar os mesmos relatórios em train2017** (não só val) e comparar deltas (train vs val).

