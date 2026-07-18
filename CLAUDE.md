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

## Stack

- Camada de IA: Python + FastAPI. Front (fase 4+): Next.js/TypeScript.
