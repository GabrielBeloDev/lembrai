# lembrai

A personal assistant that knows your stuff and acts on your behalf — profile, notes, calendar, and proactive reminders.

This is a learning-in-public project: building from LLM basics up to RAG, agents, evals, and LLMOps, one phase at a time. The roadmap (pt-BR) lives in [ROADMAP.md](./ROADMAP.md).

**Privacy by architecture**: your real data never leaves your machine (`data/`, git-ignored). The repo ships only the product and a fictional demo corpus.

**Status**: phase 4b.1 — chat over HTTP (thin FastAPI service).

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

The assistant can also act on your behalf via function calling: it creates and
lists events on a local calendar (`data/calendar.json`), writes emails to a
local outbox (`data/outbox/`), and schedules reminders (`data/reminders.json`) —
real delivery and Google integration come in a later phase. Every tool execution
is shown in the terminal as it happens.

## Reminders

Ask the assistant to remind you of something ("me lembra amanhã às 10h de ligar
pro dentista") and it schedules a reminder. Due reminders are delivered when you
start `lembrai`, and by the `lembrai-check` command, which prints anything due and
marks it delivered so it never fires twice. Run it on a schedule to be reminded
even when the chat is closed — e.g. every 15 minutes via cron:

```cron
*/15 * * * * cd /path/to/lembrai && .venv/bin/lembrai-check
```

All personal data lives under `data/`, which never leaves your machine.

## API

The same assistant is also exposed over HTTP by a thin, stateless FastAPI service —
the streaming groundwork for the web front (phase 4b). Install the API extras and run it:

```bash
.venv/bin/pip install -e ".[dev,api]"
.venv/bin/lembrai-api   # serves on http://127.0.0.1:8000
```

`POST /chat` takes `{"messages": [{"role", "content"}, ...]}` and streams the reply as
Server-Sent Events (`token`, `tool`, `tool_result`, `done`, `error`). The server keeps no
session: the client owns the history and sends it on every request. `GET /health` returns
`{"status": "ready"}` once the embedding model is loaded. The `GROQ_API_KEY` stays on the
server (in its `.env`) and is never exposed to the browser.

Run the tests with `.venv/bin/pytest`.
