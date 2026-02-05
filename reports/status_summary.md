# Status Summary — NextNutri BodyComp MVP

Gerado em: **2026-02-05 13:03:19 UTC**
Git: **main @ 292b8c3**

## Dataset (COCO 2017)
- train2017: **118.287** imagens
- val2017: **5.000** imagens

## Infra / Disco
- `df -h /`: `/dev/sda1        99G   33G   62G  35% /`

## Worker (estado)
- tick: **161**
- última ação: **rodei pose em ROI sample 1000 (ok=615, no_pose=385)**
- próxima ação: **aumentar sample p/ 1000 + quality gates**

## Últimas ações (log)
- tick 161 [ok]: rodei pose em ROI sample 1000 (ok=615, no_pose=385) → próximo: aumentar sample p/ 1000 + quality gates
- tick 160 [ok]: gerei ROIs via keypoints (pad=0.15) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 159 [ok]: rodei pose em ROI sample 1000 (ok=653, no_pose=347) → próximo: aumentar sample p/ 1000 + quality gates
- tick 158 [ok]: quality gates - ok: **247** - reject: **753** → próximo: ajustar ROI pad e rerodar quality gates
- tick 157 [ok]: rodei pose em ROI sample 1000 (ok=653, no_pose=347) → próximo: aumentar sample p/ 1000 + quality gates
- tick 156 [ok]: quality gates - ok: **247** - reject: **753** → próximo: ajustar ROI pad e rerodar quality gates
- tick 155 [ok]: gerei ROIs via keypoints (pad=0.25) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 154 [ok]: quality gates - ok: **281** - reject: **719** → próximo: ajustar ROI pad e rerodar quality gates
- tick 153 [ok]: rodei pose em ROI sample 1000 (ok=673, no_pose=327) → próximo: aumentar sample p/ 1000 + quality gates
- tick 152 [ok]: quality gates - ok: **210** - reject: **790** → próximo: ajustar ROI pad e rerodar quality gates
- tick 151 [ok]: rodei pose em ROI sample 1000 (ok=615, no_pose=385) → próximo: aumentar sample p/ 1000 + quality gates
- tick 150 [ok]: gerei ROIs via keypoints (pad=0.15) → próximo: rodar pose em ROI sample 1000 e comparar vs full

## Artefatos recentes
- Quality gates (mais recente): `reports/quality_eval_pad025_rerun.md`
- Quality gates (dados): `reports/quality_eval_pad025_rerun.jsonl`
- ROI vs Full (val): `reports/coco_val2017_pose_roi_vs_full.md`

## Leitura humana (o que isso significa)
- A gente já tem **COCO train+val** localmente, então dá pra parar de 'smoke test' e começar a medir estabilidade com amostras maiores.
- O worker está rodando num ciclo simples (ROI list ↔ pose em ROI ↔ quality gates).
- Próximo upgrade é: **rodar os mesmos relatórios em train2017** (não só val) e comparar deltas (train vs val).

