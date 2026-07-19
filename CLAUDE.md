# lembrai — convenções do repo

## Git

- Repo público. Commits e títulos de PR em inglês; a descrição da PR pode ser em português.
- Nunca adicionar Co-Authored-By ou créditos de IA em commits e PRs.
- `.env` nunca entra no repo.

## Dados

- Dados reais do Usuário vivem em `data/` (fora do git). Nunca commitar dados pessoais.
- O que se versiona é o produto + o Corpus de Demo (fictício), em `demo/`.

## Domínio

- Vocabulário canônico em `CONTEXT.md` — usar esses termos em código, docs e PRs.
- Plano de fases e decisões em `ROADMAP.md`; decisões arquiteturais em `docs/adr/`.

## Comentários

- Comentar só para explicar um fluxo de exceção: um caso especial, edge case ou caminho
  não-óbvio que o código limpo sozinho não revela (por que existe um early-return, um
  workaround, uma decisão contraintuitiva).
- Código limpo não precisa de comentário — nomes de classes, funções e variáveis devem bastar.
- Nunca comentar o que o código já diz. Quando comentar, em inglês.

## Stack

- Camada de IA: Python + FastAPI. Front (fase 4+): Next.js/TypeScript.
