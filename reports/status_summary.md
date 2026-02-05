# Status Summary — NextNutri BodyComp MVP

Gerado em: **2026-02-05 14:13:43 UTC**
Git: **main @ 0cbba79**

## Dataset (COCO 2017)
- train2017: **118.287** imagens
- val2017: **5.000** imagens

## Infra / Disco
- `df -h /`: `/dev/sda1        99G   33G   62G  35% /`

## Worker (estado)
- tick: **215**
- última ação: **gerei ROIs via keypoints (pad=0.25)**
- próxima ação: **rodar pose em ROI sample 1000 e comparar vs full**

## Últimas ações (log)
- tick 215 [ok]: gerei ROIs via keypoints (pad=0.25) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 214 [ok]: quality gates - ok: **210** - reject: **790** → próximo: ajustar ROI pad e rerodar quality gates
- tick 213 [ok]: rodei pose em ROI sample 1000 (ok=615, no_pose=385) → próximo: aumentar sample p/ 1000 + quality gates
- tick 212 [ok]: quality gates - ok: **210** - reject: **790** → próximo: ajustar ROI pad e rerodar quality gates
- tick 211 [ok]: rodei pose em ROI sample 1000 (ok=615, no_pose=385) → próximo: aumentar sample p/ 1000 + quality gates
- tick 210 [ok]: gerei ROIs via keypoints (pad=0.15) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 209 [ok]: rodei pose em ROI sample 1000 (ok=653, no_pose=347) → próximo: aumentar sample p/ 1000 + quality gates
- tick 208 [ok]: quality gates - ok: **247** - reject: **753** → próximo: ajustar ROI pad e rerodar quality gates
- tick 207 [ok]: rodei pose em ROI sample 1000 (ok=653, no_pose=347) → próximo: aumentar sample p/ 1000 + quality gates
- tick 206 [ok]: quality gates - ok: **247** - reject: **753** → próximo: ajustar ROI pad e rerodar quality gates
- tick 205 [ok]: gerei ROIs via keypoints (pad=0.25) → próximo: rodar pose em ROI sample 1000 e comparar vs full
- tick 204 [ok]: quality gates - ok: **210** - reject: **790** → próximo: ajustar ROI pad e rerodar quality gates

## Artefatos recentes
- Quality gates (mais recente): `reports/quality_eval.md`
- Quality gates (dados): `reports/quality_eval.jsonl`
- Quality gates (train n=1000): `reports/quality_eval_train_n1000.md`
- Quality gates (val n=1000): `reports/quality_eval_n1000.md`
- ROI vs Full (val): `reports/coco_val2017_pose_roi_vs_full.md`

## Leitura humana (o que isso significa)
- A gente já tem **COCO train+val** localmente, então dá pra parar de 'smoke test' e começar a medir estabilidade com amostras maiores.
- O worker está rodando num ciclo simples (ROI list ↔ pose em ROI ↔ quality gates).
- Próximo upgrade é: **rodar os mesmos relatórios em train2017** (não só val) e comparar deltas (train vs val).

