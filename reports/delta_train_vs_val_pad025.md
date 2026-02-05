# Delta — Train vs Val (pad=0.25)

## Summary
- train: ok=1239 reject=3761
- val:   ok=1256 reject=3744

## Top reject reasons (train)
- too_blurry: Foto tremida/desfocada. Apoie o celular, use temporizador e tente de novo.
- too_bright: Foto estourada (muita luz). Afaste da luz direta e tente de novo.
- too_dark: Foto escura. Vire para a luz / aumente iluminação e tente de novo.
- too_small: A pessoa está pequena no frame. Chegue mais perto e deixe o corpo inteiro visível.

## Top reject reasons (val)
- too_blurry: Foto tremida/desfocada. Apoie o celular, use temporizador e tente de novo.
- too_bright: Foto estourada (muita luz). Afaste da luz direta e tente de novo.
- too_dark: Foto escura. Vire para a luz / aumente iluminação e tente de novo.
- too_small: A pessoa está pequena no frame. Chegue mais perto e deixe o corpo inteiro visível.

## Interpretação
- Se `too_small` dominar nos dois splits, o gargalo é enquadramento/tamanho do ROI.
- A próxima etapa é sweep de thresholds para aumentar aceitação sem perder qualidade.
