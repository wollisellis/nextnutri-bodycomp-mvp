# Contrato (NLP) — /estimate quality

Quando a foto for rejeitada, o endpoint responde 422 com detail estruturado:

detail = {quality_ok, quality_reason, quality_message_ptbr}

Reasons iniciais:
- precheck (luz/blur)
- no_pose
- too_small
