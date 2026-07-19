import json
from pathlib import Path
from types import SimpleNamespace

from conftest import RecordingClient, content_chunk, final_chunk, tool_call_chunk

from lembrai.agent import run_agent_turn
from lembrai.tools import TOOL_SCHEMAS, Toolbox


class AlwaysToolClient:
    def __init__(self):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_: iter(
                    [tool_call_chunk(0, call_id="c", name="list_events",
                                     arguments="{}")]
                )
            )
        )


def make_toolbox(tmp_path: Path) -> Toolbox:
    return Toolbox(
        calendar_path=tmp_path / "calendar.json",
        outbox_dir=tmp_path / "outbox",
        reminders_path=tmp_path / "reminders.json",
    )


def run(
    client,
    toolbox,
    on_chunk=None,
    on_tool=None,
    on_malformed_tool=None,
    on_tool_result=None,
):
    return run_agent_turn(
        client,
        [{"role": "user", "content": "faz algo"}],
        toolbox,
        on_chunk=on_chunk or (lambda _: None),
        on_tool=on_tool or (lambda _name, _args: None),
        on_malformed_tool=on_malformed_tool or (lambda _name: None),
        on_tool_result=on_tool_result or (lambda _name, _result: None),
    )


def test_tool_call_is_executed_and_wire_format_is_correct(tmp_path: Path):
    arguments = json.dumps(
        {"title": "Dentista", "date": "2026-07-25", "time": "14:00"}
    )
    client = RecordingClient(
        [
            [
                content_chunk("Vou marcar."),
                tool_call_chunk(0, call_id="call_1", name="create_event",
                                arguments=arguments),
                final_chunk(30, 10),
            ],
            [content_chunk("Marquei o dentista!"), final_chunk(50, 12)],
        ]
    )
    seen: list[str] = []
    executed: list[tuple[str, dict[str, object]]] = []
    text, usages = run(
        client,
        make_toolbox(tmp_path),
        on_chunk=seen.append,
        on_tool=lambda name, args: executed.append((name, args)),
    )

    assert text == "Marquei o dentista!"
    assert seen == ["Vou marcar.", "Marquei o dentista!"]
    assert executed == [
        ("create_event", {"title": "Dentista", "date": "2026-07-25",
                          "time": "14:00"})
    ]
    assert len(usages) == 2

    events = json.loads((tmp_path / "calendar.json").read_text(encoding="utf-8"))
    assert events[0]["title"] == "Dentista"

    assert client.calls[0]["tools"] is TOOL_SCHEMAS
    second_round = client.calls[1]["messages"]
    assistant = second_round[-2]
    tool_result = second_round[-1]
    assert assistant["role"] == "assistant"
    assert assistant["content"] == "Vou marcar."
    assert assistant["tool_calls"] == [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "create_event", "arguments": arguments},
        }
    ]
    assert tool_result["role"] == "tool"
    assert tool_result["tool_call_id"] == "call_1"
    assert tool_result["name"] == "create_event"
    assert "Evento criado" in tool_result["content"]


def test_every_tool_call_in_a_round_gets_a_paired_result(tmp_path: Path):
    create_arguments = json.dumps({"title": "Dentista", "date": "2026-07-25"})
    client = RecordingClient(
        [
            [
                tool_call_chunk(0, call_id="call_a", name="create_event",
                                arguments=create_arguments),
                tool_call_chunk(1, call_id="call_b", name="list_events",
                                arguments="{}"),
            ],
            [content_chunk("Feito.")],
        ]
    )
    executed: list[str] = []
    text, _ = run(
        client,
        make_toolbox(tmp_path),
        on_tool=lambda name, _args: executed.append(name),
    )
    assert text == "Feito."
    assert executed == ["create_event", "list_events"]
    tool_messages = [
        message
        for message in client.calls[1]["messages"]
        if message.get("role") == "tool"
    ]
    assert [message["tool_call_id"] for message in tool_messages] == [
        "call_a",
        "call_b",
    ]


def test_malformed_arguments_do_not_reach_the_toolbox(tmp_path: Path):
    client = RecordingClient(
        [
            [tool_call_chunk(0, call_id="call_1", name="create_event",
                             arguments="not json")],
            [content_chunk("Não consegui.")],
        ]
    )
    executed: list[str] = []
    malformed: list[str] = []
    text, _ = run(
        client,
        make_toolbox(tmp_path),
        on_tool=lambda name, _args: executed.append(name),
        on_malformed_tool=malformed.append,
    )
    assert text == "Não consegui."
    assert executed == []
    assert malformed == ["create_event"]
    assert not (tmp_path / "calendar.json").exists()
    tool_result = client.calls[1]["messages"][-1]
    assert tool_result["role"] == "tool"
    assert "Argumentos inválidos" in tool_result["content"]


def test_agent_gives_up_after_the_round_limit(tmp_path: Path):
    text, _ = run(AlwaysToolClient(), make_toolbox(tmp_path))
    assert text is None


def test_tool_result_is_reported_after_the_tool_call(tmp_path: Path):
    client = RecordingClient(
        [
            [tool_call_chunk(0, call_id="call_1", name="list_events",
                             arguments="{}")],
            [content_chunk("Pronto.")],
        ]
    )
    events: list[tuple[str, str]] = []
    run(
        client,
        make_toolbox(tmp_path),
        on_tool=lambda name, _args: events.append(("tool", name)),
        on_tool_result=lambda name, _result: events.append(("tool_result", name)),
    )
    assert events == [("tool", "list_events"), ("tool_result", "list_events")]
