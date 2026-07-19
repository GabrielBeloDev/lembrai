# lembrai

A personal assistant that knows your stuff and acts on your behalf — profile, notes, calendar, and proactive reminders.

This is a learning-in-public project: building from LLM basics up to RAG, agents, evals, and LLMOps, one phase at a time. The roadmap (pt-BR) lives in [ROADMAP.md](./ROADMAP.md).

**Privacy by architecture**: your real data never leaves your machine (`data/`, git-ignored). The repo ships only the product and a fictional demo corpus.

**Status**: phase 5b — optional Langfuse observability (phase 5 complete).

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
Server-Sent Events: `token` (text delta), `tool` / `tool_result` / `tool_error` (a tool
call, its result, or malformed arguments — non-terminal), `done` (final text plus token
usage and cost), and `error` (terminal). The server keeps no
session: the client owns the history and sends it on every request. `GET /health` returns
`{"status": "ready"}` once the embedding model is loaded. The `GROQ_API_KEY` stays on the
server (in its `.env`) and is never exposed to the browser.

Alongside chat, the service exposes plain REST endpoints for the rest of the product
(profile, notes and reminders), all reading and writing the same local `data/`:

- `GET /profile` → `{"content": string | null}`; `POST /profile` `{"answers": [...]}` builds
  and persists the profile from the onboarding answers (blank answers are skipped).
- `GET /onboarding/questions` → the onboarding form questions, in order.
- `POST /notes` `{"text": ...}` saves a note and returns its `id`; `GET /notes` lists saved
  notes, most recent first.
- `GET /reminders` lists all reminders (by due date); `POST /reminders/deliver` delivers the
  ones due now and returns their messages (idempotent).

## Web

A minimal Next.js (App Router, TypeScript) front-end (`web/`) for the whole product,
organized as tabs — **Chat**, **Notas**, **Lembretes** and **Perfil**. Every request goes
through a same-origin Next `rewrite` (`/api/ai/*` → FastAPI), so the backend origin never
leaks and the `GROQ_API_KEY` stays on the server.

- **Chat** streams from `/api/ai/chat`: the client owns the conversation history, renders the
  reply token by token, and shows tool activity live.
- **Notas** lists your notes and adds new ones (optimistic insert, then reconciled against the
  server; empty notes are rejected).
- **Lembretes** lists reminders (message, due date, delivered/pending) and has a "Verificar
  vencidos" button that delivers the ones due now.
- **Perfil** shows your profile, or the onboarding form when you don't have one yet — answer
  the questions to build it, and reopen the form anytime to edit.

Each tab fetches its data on demand the first time it is opened (there is no data-fetching on
mount); a typed API client (`web/lib/api.ts`) parses every response with type guards. Run the
full stack locally with two terminals:

```bash
# terminal 1 — the API (holds the GROQ_API_KEY)
.venv/bin/pip install -e ".[dev,api]"
.venv/bin/lembrai-api            # serves on http://127.0.0.1:8000

# terminal 2 — the web front
cd web
npm install
npm run dev                      # http://localhost:3000
```

## Evals

A small eval harness measures whether the assistant answers correctly over the fictional
demo corpus (`demo/` — a made-up profile and notes, versioned for public demos and evals).
It asks each question in `demo/qa.json`, runs the same retrieve-and-answer path as the chat,
and scores the reply:

- **fact / profile** questions: the expected answer must appear in the reply (case- and
  whitespace-insensitive); on a miss, an LLM-as-judge decides whether a paraphrase is still
  factually correct against the reference.
- **refusal** questions (answers the corpus does not contain): the reply passes only if the
  assistant admits it doesn't know instead of hallucinating.

Honest caveat: for fact / profile, a substring hit is accepted without consulting the judge
(a non-discriminating fast path), so the accuracy number for those kinds is not fully
judge-verified; refusals are always judged.

Run it (it indexes the demo notes into a throwaway directory, so it never touches `data/`):

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/lembrai-eval
```

It prints the overall accuracy, a breakdown by question kind, and every failure (the
question, the expected answer, and the reply it got).

## Observability (optional)

Chat turns can be traced to [Langfuse](https://langfuse.com) — input/output, model, token
usage, estimated cost and latency, one trace per turn. It is fully optional and off by
default: without the keys (or without the package installed) the instrumentation is a
silent no-op and nothing about the app changes.

Enable it by installing the extra and setting the keys in your `.env`:

```bash
.venv/bin/pip install -e ".[observability]"
```

```dotenv
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com   # or http://localhost:3000 to self-host
```

Point it at [Langfuse Cloud](https://cloud.langfuse.com) or a self-hosted instance (their
Docker Compose). Traces go only to whichever Langfuse you configure — nothing leaves your
machine unless you set the keys yourself. The CLI flushes pending traces on exit; the
long-lived API server lets Langfuse batch them in the background.

## Fine-tuning experiment (optional)

A side lab in [`finetune/`](./finetune/) fine-tunes a small 4-bit model (LoRA, via MLX)
to the lembrai answer style, running fully local on Apple Silicon. It is a learning
experiment — not wired into the product (which stays on Groq), and `mlx-lm` is not a
lembrai dependency. See [`finetune/README.md`](./finetune/README.md) for the concepts,
how to run it, and the real results (loss curve and before/after generations).

Run the tests with `.venv/bin/pytest`.
