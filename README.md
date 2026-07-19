# lembrai

A personal assistant that knows your stuff and acts on your behalf — profile, notes, calendar, and proactive reminders.

This is a learning-in-public project: building from LLM basics up to RAG, agents, evals, and LLMOps, one phase at a time. The roadmap (pt-BR) lives in [ROADMAP.md](./ROADMAP.md).

**Privacy by architecture**: your real data never leaves your machine (`data/`, git-ignored). The repo ships only the product and a fictional demo corpus.

**Status**: phase 1 — Conversa (chat CLI).

## Getting started

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
echo "GROQ_API_KEY=your_key_here" > .env   # get one at console.groq.com
.venv/bin/lembrai
```

Optionally, create `data/profile.md` with a few lines about yourself — the assistant
uses it to personalize every answer. Inside the chat: `/stats` shows session token
usage and cost, `/limpar` clears the history, `/sair` exits.

Run the tests with `.venv/bin/pytest`.
