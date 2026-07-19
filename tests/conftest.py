from types import SimpleNamespace


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


class RecordingClient:
    """Scripted streams, one per create() call; records every call's kwargs."""

    def __init__(self, streams: list[list[SimpleNamespace]]):
        self._streams = iter(streams)
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs) -> object:
        self.calls.append(kwargs)
        return iter(next(self._streams))
