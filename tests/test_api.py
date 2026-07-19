import json
from pathlib import Path

import pytest
from conftest import RecordingClient, content_chunk, final_chunk, tool_call_chunk
from fastapi.testclient import TestClient

from lembrai.api import Deps, app, get_deps
from lembrai.embeddings import Embedder
from lembrai.notes import NoteStore
from lembrai.tools import Toolbox

FAKE_EMBEDDER = Embedder(
    embed_queries=lambda texts: [[0.0] for _ in texts],
    embed_passages=lambda texts: [[0.0] for _ in texts],
)


def make_deps(recording: RecordingClient, tmp_path: Path) -> Deps:
    return Deps(
        client=recording,
        note_store=NoteStore(
            embedder=FAKE_EMBEDDER,
            notes_dir=tmp_path / "notes",
            chroma_dir=tmp_path / "chroma",
        ),
        toolbox=Toolbox(
            calendar_path=tmp_path / "calendar.json",
            outbox_dir=tmp_path / "outbox",
            reminders_path=tmp_path / "reminders.json",
        ),
    )


@pytest.fixture
def chat_client(tmp_path: Path):
    def build(recording: RecordingClient) -> TestClient:
        deps = make_deps(recording, tmp_path)
        app.dependency_overrides[get_deps] = lambda: deps
        return TestClient(app)

    yield build
    app.dependency_overrides.clear()


def parse_sse(body: str) -> list[tuple[str, dict[str, object]]]:
    frames: list[tuple[str, dict[str, object]]] = []
    for block in body.split("\n\n"):
        if not block.strip():
            continue
        event = ""
        data = ""
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line.removeprefix("event: ")
            elif line.startswith("data: "):
                data = line.removeprefix("data: ")
        frames.append((event, json.loads(data)))
    return frames


def post_chat(client: TestClient, text: str):
    return client.post("/chat", json={"messages": [{"role": "user", "content": text}]})


def test_simple_response_streams_tokens_then_done(chat_client):
    recording = RecordingClient(
        [[content_chunk("Oi"), content_chunk(", tudo bem?"), final_chunk(10, 4)]]
    )
    response = post_chat(chat_client(recording), "oi")

    assert response.status_code == 200
    frames = parse_sse(response.text)
    assert [event for event, _ in frames] == ["token", "token", "done"]
    assert frames[0][1] == {"text": "Oi"}
    assert frames[1][1] == {"text": ", tudo bem?"}
    done = frames[-1][1]
    assert done["text"] == "Oi, tudo bem?"
    assert done["usage"]["prompt_tokens"] == 10
    assert done["usage"]["completion_tokens"] == 4
    assert done["usage"]["total_tokens"] == 14
    assert done["usage"]["cost_usd"] is not None


def test_tool_call_turn_streams_tool_result_then_answer(chat_client):
    recording = RecordingClient(
        [
            [
                content_chunk("Deixa eu ver."),
                tool_call_chunk(0, call_id="c1", name="list_events",
                                arguments="{}"),
                final_chunk(12, 3),
            ],
            [content_chunk("Sua agenda está vazia."), final_chunk(20, 6)],
        ]
    )
    response = post_chat(chat_client(recording), "o que tenho hoje?")

    assert response.status_code == 200
    frames = parse_sse(response.text)
    assert [event for event, _ in frames] == [
        "token",
        "tool",
        "tool_result",
        "token",
        "done",
    ]
    assert frames[1][1] == {"name": "list_events", "arguments": {}}
    result = frames[2][1]
    assert result["name"] == "list_events"
    assert "agenda" in result["result"]
    assert frames[-1][1]["text"] == "Sua agenda está vazia."


def test_health_reports_ready(chat_client):
    response = chat_client(RecordingClient([])).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
