import json
from pathlib import Path
from types import SimpleNamespace

from lembrai.agent import run_agent_turn
from lembrai.tools import Toolbox
from tests.test_chat import content_chunk, final_chunk, tool_call_chunk


class ScriptedClient:
    def __init__(self, streams: list[list[SimpleNamespace]]):
        self._streams = iter(streams)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_: iter(next(self._streams))
            )
        )


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
    )


def test_tool_call_is_executed_and_final_text_returned(tmp_path: Path):
    arguments = json.dumps(
        {"title": "Dentista", "date": "2026-07-25", "time": "14:00"}
    )
    client = ScriptedClient(
        [
            [
                tool_call_chunk(0, call_id="call_1", name="create_event",
                                arguments=arguments),
                final_chunk(30, 10),
            ],
            [content_chunk("Marquei o dentista!"), final_chunk(50, 12)],
        ]
    )
    executed: list[tuple[str, dict[str, str]]] = []
    text, usages = run_agent_turn(
        client,
        [{"role": "user", "content": "marca dentista"}],
        make_toolbox(tmp_path),
        on_chunk=lambda _: None,
        on_tool=lambda name, args: executed.append((name, args)),
    )
    assert text == "Marquei o dentista!"
    assert executed == [
        ("create_event", {"title": "Dentista", "date": "2026-07-25",
                          "time": "14:00"})
    ]
    events = json.loads((tmp_path / "calendar.json").read_text(encoding="utf-8"))
    assert events[0]["title"] == "Dentista"
    assert len(usages) == 2


def test_malformed_arguments_do_not_reach_the_toolbox(tmp_path: Path):
    client = ScriptedClient(
        [
            [tool_call_chunk(0, call_id="call_1", name="create_event",
                             arguments="not json")],
            [content_chunk("Não consegui.")],
        ]
    )
    executed: list[str] = []
    text, _ = run_agent_turn(
        client,
        [{"role": "user", "content": "marca"}],
        make_toolbox(tmp_path),
        on_chunk=lambda _: None,
        on_tool=lambda name, _args: executed.append(name),
    )
    assert text == "Não consegui."
    assert executed == []
    assert not (tmp_path / "calendar.json").exists()


def test_agent_gives_up_after_the_round_limit(tmp_path: Path):
    text, _ = run_agent_turn(
        AlwaysToolClient(),
        [{"role": "user", "content": "lista"}],
        make_toolbox(tmp_path),
        on_chunk=lambda _: None,
        on_tool=lambda _name, _args: None,
    )
    assert text is None
