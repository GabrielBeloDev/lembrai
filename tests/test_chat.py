from types import SimpleNamespace

from lembrai.chat import stream_reply
from lembrai.cost import Usage


def content_chunk(text: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text))],
        x_groq=None,
    )


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
    reply, usage = stream_reply(client, [], on_chunk=seen.append)
    assert reply == "Olá, Gabriel"
    assert seen == ["Olá", ", Gabriel"]
    assert usage == Usage(prompt_tokens=10, completion_tokens=5, total_time=0.5)


def test_usage_is_none_when_stream_never_sends_it():
    client = FakeGroq([content_chunk("oi")])
    reply, usage = stream_reply(client, [], on_chunk=lambda _: None)
    assert reply == "oi"
    assert usage is None


def test_empty_deltas_are_skipped():
    client = FakeGroq([content_chunk(None), content_chunk("oi"), final_chunk(1, 1)])
    seen: list[str] = []
    reply, _ = stream_reply(client, [], on_chunk=seen.append)
    assert reply == "oi"
    assert seen == ["oi"]
