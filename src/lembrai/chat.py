from collections.abc import Callable

from groq import Groq

from lembrai.cost import Usage
from lembrai.history import Message

MODEL = "llama-3.3-70b-versatile"


def stream_reply(
    client: Groq,
    messages: list[Message],
    on_chunk: Callable[[str], None],
) -> tuple[str, Usage | None]:
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
    )
    parts: list[str] = []
    usage: Usage | None = None
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content
            parts.append(delta)
            on_chunk(delta)
        # usage arrives only on the final chunk, via Groq's x_groq extension
        if chunk.x_groq and chunk.x_groq.usage:
            usage = Usage(
                prompt_tokens=chunk.x_groq.usage.prompt_tokens,
                completion_tokens=chunk.x_groq.usage.completion_tokens,
                total_time=chunk.x_groq.usage.total_time,
            )
    return "".join(parts), usage
