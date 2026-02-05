# Recomendação — gate/fallback para ROI crops (pose)

Baseado em:
- `reports/pose_roi_failure_vs_size.md` (amostra n=1000)
- `reports/coco_val2017_pose_roi_vs_full.md` (comparação ROI vs full)

## Observação
As falhas de pose (`no_pose`) aumentam bastante quando o ROI é pequeno.
Na amostra:
- `ok`: p05 minSide ≈ 32.5 px
- `no_pose`: p25 minSide ≈ 29.9 px (e casos extremos minSide ~1–2 px)

## Gate simples sugerido (alto ROI)
Antes de rodar pose no crop, calcule:
- `minSide = min(w, h)` do bbox/ROI (em pixels)

Regras:
1) Se `minSide < 32 px`: **não** rodar pose no crop; fazer **fallback** para pose na imagem cheia.
2) Caso contrário: rodar pose no ROI crop.

## Intuição
- T=32 rejeita ~28.8% dos `no_pose` com custo baixo (~4.4% dos `ok` seriam desviados pro fallback)
- Isso tende a reduzir tempo perdido em crops inviáveis e aumentar taxa de sucesso geral.

## Próximo experimento
Rodar novamente o pipeline em uma amostra maior (ex.: 2000–5000) com:
- ROI pose com gate (T=32)
- fallback full
E comparar:
- taxa `ok`
- tempo total
- casos onde ROI melhora vs piora.
