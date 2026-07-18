# lembrai

A personal assistant that knows your stuff and acts on your behalf — profile, notes, calendar, and proactive reminders.

This is a learning-in-public project: building from LLM basics up to RAG, agents, evals, and LLMOps, one phase at a time. The roadmap (pt-BR) lives in [ROADMAP.md](./ROADMAP.md).

**Privacy by architecture**: your real data never leaves your machine (`data/`, git-ignored). The repo ships only the product and a fictional demo corpus.

**Status**: phase 2 — Memória (Perfil + Notas with local RAG).

## Getting started

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
echo "GROQ_API_KEY=your_key_here" > .env   # get one at console.groq.com
.venv/bin/lembrai
```

On first run the assistant offers a short onboarding form that builds your profile
(`data/profile.md` — edit it anytime), and downloads a small multilingual embedding
model (~120 MB, one time) for semantic note search.

Inside the chat: `/nota <text>` saves a note (stored in `data/notes/`, embedded
locally into ChromaDB at `data/chroma/`), and every message you send retrieves your
most relevant notes so the assistant can use them. `/stats` shows session token usage
and cost, `/limpar` clears the history, `/sair` exits.

All personal data lives under `data/`, which never leaves your machine.

Run the tests with `.venv/bin/pytest`.
