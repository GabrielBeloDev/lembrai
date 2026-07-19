import json
import logging
import queue
import threading
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import StreamingResponse
from groq import APIError, Groq
from pydantic import BaseModel, Field, field_validator

from lembrai.agent import run_agent_turn
from lembrai.chat import MODEL
from lembrai.check import due_messages
from lembrai.cli import create_client
from lembrai.cost import Usage, combined_usage, estimated_cost_usd
from lembrai.embeddings import create_embedder
from lembrai.history import Message, trimmed
from lembrai.notes import NoteStore, StoredNote, as_context
from lembrai.onboarding import QUESTIONS, ask_profile, save_profile
from lembrai.profile import build_system_prompt, load_profile
from lembrai.reminders import Reminder, ReminderStore
from lembrai.tools import Toolbox

logger = logging.getLogger(__name__)

SseEvent = tuple[str, dict[str, object]]


@dataclass
class Deps:
    client: Groq
    note_store: NoteStore
    reminder_store: ReminderStore
    toolbox: Toolbox


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)


class ProfileRequest(BaseModel):
    answers: list[str]


class NoteRequest(BaseModel):
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a nota não pode ser vazia")
        return value


class ProfileResponse(BaseModel):
    content: str | None


class Question(BaseModel):
    title: str
    question: str


class NoteCreated(BaseModel):
    id: str


class DeliveredReminders(BaseModel):
    delivered: list[str]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.deps = Deps(
        client=create_client(),
        note_store=NoteStore(embedder=create_embedder()),
        reminder_store=ReminderStore(),
        toolbox=Toolbox(),
    )
    yield


app = FastAPI(lifespan=lifespan)


def get_deps(request: Request) -> Deps:
    return request.app.state.deps


def _build_messages(note_store: NoteStore, body: ChatRequest) -> list[Message]:
    messages: list[Message] = [
        {"role": "system", "content": build_system_prompt(load_profile())}
    ]
    matches = note_store.search(body.messages[-1].content)
    if matches:
        messages.append({"role": "system", "content": as_context(matches)})
    history: list[Message] = [
        {"role": message.role, "content": message.content}
        for message in body.messages
    ]
    messages.extend(trimmed(history))
    return messages


@app.post("/chat")
def chat(body: ChatRequest, deps: Deps = Depends(get_deps)) -> StreamingResponse:
    base_messages = _build_messages(deps.note_store, body)

    def gen() -> Iterator[str]:
        events: queue.Queue[SseEvent | None] = queue.Queue()

        def emit(event: str, payload: dict[str, object]) -> None:
            events.put((event, payload))

        def run() -> None:
            try:
                text, usages = run_agent_turn(
                    deps.client,
                    base_messages,
                    deps.toolbox,
                    on_chunk=lambda token: emit("token", {"text": token}),
                    on_tool=lambda name, arguments: emit(
                        "tool", {"name": name, "arguments": arguments}
                    ),
                    on_tool_result=lambda name, result: emit(
                        "tool_result", {"name": name, "result": result}
                    ),
                    on_malformed_tool=lambda name: emit(
                        "tool_error", {"name": name}
                    ),
                )
                if text is None:
                    emit("error", {"message": "limite de rodadas de ferramenta atingido"})
                else:
                    usage = combined_usage(usages)
                    emit(
                        "done",
                        {"text": text, "usage": _usage_payload(usage)},
                    )
            except APIError as error:
                emit("error", {"message": error.message})
            except Exception:
                logger.exception("chat turn failed")
                emit("error", {"message": "erro interno ao processar a conversa"})
            finally:
                # sentinel: unblocks the consumer drain loop below; without it
                # events.get() would block forever once the worker finishes
                events.put(None)

        threading.Thread(target=run, daemon=True).start()
        while True:
            item = events.get()
            if item is None:
                break
            event, payload = item
            yield f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _usage_payload(usage: Usage | None) -> dict[str, object] | None:
    if usage is None:
        return None
    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "cost_usd": estimated_cost_usd(MODEL, usage),
        "total_time": usage.total_time,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/profile")
def get_profile() -> ProfileResponse:
    return ProfileResponse(content=load_profile())


@app.get("/onboarding/questions")
def onboarding_questions() -> list[Question]:
    return [
        Question(title=title, question=question) for title, question in QUESTIONS
    ]


@app.post("/profile")
def create_profile(body: ProfileRequest) -> ProfileResponse:
    answers = iter(body.answers)
    content = ask_profile(ask=lambda _question: next(answers, ""))
    if content is not None:
        save_profile(content)
    return ProfileResponse(content=content)


@app.post("/notes")
def create_note(body: NoteRequest, deps: Deps = Depends(get_deps)) -> NoteCreated:
    path = deps.note_store.add(body.text)
    return NoteCreated(id=path.stem)


@app.get("/notes")
def list_notes(deps: Deps = Depends(get_deps)) -> list[StoredNote]:
    return deps.note_store.list_notes()


@app.get("/reminders")
def list_reminders(deps: Deps = Depends(get_deps)) -> list[Reminder]:
    return sorted(deps.reminder_store.all(), key=lambda reminder: reminder.due)


@app.post("/reminders/deliver")
def deliver_reminders(deps: Deps = Depends(get_deps)) -> DeliveredReminders:
    return DeliveredReminders(
        delivered=due_messages(deps.reminder_store, datetime.now())
    )


def main() -> None:
    uvicorn.run("lembrai.api:app", host="127.0.0.1", port=8000)
