# Faraday Ops — Controle de Projetos (GitHub)

## Kanban (visual) — Trello (recomendado)
- Board: **Faraday Ops**
- URL: https://trello.com/b/tZC0cpyh/faraday-ops
- Colunas: Inbox / Todo / Doing / Done

## Kanban (GitHub Project) — dev/issues
- Project: **Faraday Ops**
- URL: https://github.com/users/wollisellis/projects/3

## Como usar
1) Crie tasks como **Issues** no repo.
2) Use os **templates** (aba *New issue*): PRISMA, Finanças, Conteúdo, Browser, DevOps.
3) O Project puxa as issues e você acompanha em *Todo / In Progress / Done*.

## Status (field)
- Todo
- In Progress
- Done

> Nota: eu tentei renomear as colunas para Backlog/Doing/Blocked/Done, mas a API do GitHub Projects v2 (via GraphQL) não aceitou a mutation de update de opções no ambiente atual. A estrutura padrão (Todo/In Progress/Done) já resolve 95% do fluxo.

## Seeds (issues iniciais)
- #1 Ops: Mission Control (Jarvis protocol)
- #2 PRISMA: Revisão 2D foto → DEXA
- #3 Finanças: CSV/relatórios
- #4 Conteúdo: CDA piloto + guidelines
- #5 Browser: coletar fontes/citações
