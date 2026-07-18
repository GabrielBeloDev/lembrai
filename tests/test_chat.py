from types import SimpleNamespace

from lembrai.chat import ToolCall, stream_reply
from lembrai.cost import Usage


def content_chunk(text: str | None) -> SimpleNamespace:
    delta = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)], x_groq=None)


def tool_call_chunk(
    index: int,
    call_id: str | None = None,
    name: str | None = None,
    arguments: str | None = None,
) -> SimpleNamespace:
    fragment = SimpleNamespace(
        index=index,
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )
    delta = SimpleNamespace(content=None, tool_calls=[fragment])
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)], x_groq=None)


def final_chunk(prompt_tokens: int, completion_tokens: int) -> SimpleNamespace:
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_time=0.5,
    )
    return SimpleNamespace(choices=[], x_groq=SimpleNamespace(usage=usage))


class FakeGroq:
    def __init__(self, chunks: list[SimpleNamespace]):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_: iter(chunks))
        )


def test_reply_joins_chunks_in_order_and_reports_usage():
    client = FakeGroq(
        [content_chunk("Olá"), content_chunk(", Gabriel"), final_chunk(10, 5)]
    )
    seen: list[str] = []
    reply = stream_reply(client, [], on_chunk=seen.append)
    assert reply.text == "Olá, Gabriel"
    assert seen == ["Olá", ", Gabriel"]
    assert reply.usage == Usage(prompt_tokens=10, completion_tokens=5, total_time=0.5)
    assert reply.tool_calls == []


def test_usage_is_none_when_stream_never_sends_it():
    client = FakeGroq([content_chunk("oi")])
    reply = stream_reply(client, [], on_chunk=lambda _: None)
    assert reply.text == "oi"
    assert reply.usage is None


def test_empty_deltas_are_skipped():
    client = FakeGroq([content_chunk(None), content_chunk("oi"), final_chunk(1, 1)])
    seen: list[str] = []
    reply = stream_reply(client, [], on_chunk=seen.append)
    assert reply.text == "oi"
    assert seen == ["oi"]


def test_tool_call_fragments_are_merged_by_index():
    client = FakeGroq(
        [
            tool_call_chunk(0, call_id="call_1", name="create_event",
                            arguments='{"title": "Denti'),
            tool_call_chunk(0, arguments='sta"}'),
            final_chunk(20, 8),
        ]
    )
    reply = stream_reply(client, [], on_chunk=lambda _: None)
    assert reply.tool_calls == [
        ToolCall(id="call_1", name="create_event", arguments='{"title": "Dentista"}')
    ]
    assert reply.text == ""


def test_multiple_tool_calls_keep_their_order():
    client = FakeGroq(
        [
            tool_call_chunk(1, call_id="call_b", name="send_email", arguments="{}"),
            tool_call_chunk(0, call_id="call_a", name="list_events", arguments="{}"),
        ]
    )
    reply = stream_reply(client, [], on_chunk=lambda _: None)
    assert [call.id for call in reply.tool_calls] == ["call_a", "call_b"]
