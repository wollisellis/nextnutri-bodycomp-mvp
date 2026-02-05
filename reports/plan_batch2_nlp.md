# Plano autônomo — Bloco 2 (Etapas 11–20)

Foco: transformar os relatórios em **mudanças no produto/API**, e iniciar o caminho do **modelo aprendido com labels humanos**.

## Etapas 11–20 (propostas)
11. Corrigir mensagem final do plan_runner + preparar logs/estado para Bloco 2
12. Fixar defaults candidatos (min_side/min_area) como artefato e tornar reproduzível
13. Aplicar ajustes de qualidade no código do backend (`bodycomp_estimator/quality.py`) (menos falso reject)
14. Gerar relatório NLP: impacto esperado das mudanças (antes/depois)
15. Treino de modelo de qualidade multi-classe com labels humanos (se existir dataset local)
16. Integração do modelo aprendido como **opcional** (fallback para gates)
17. Criar guia de coleta de fotos (Android) + checklist de enquadramento
18. Adicionar endpoint/retorno que expõe `quality_reason` de forma estruturada
19. Testes automatizados: gates + modelo carregável + mensagens PT-BR
20. Consolidar status_summary.md com progresso do plano + artefatos do Bloco 2
