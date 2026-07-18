from collections.abc import Callable
from dataclasses import dataclass

from groq import Groq

from lembrai.cost import Usage
from lembrai.history import Message

MODEL = "llama-3.3-70b-versatile"

ToolSchema = dict[str, object]


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class Reply:
    text: str
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage | None = None


def _merge_tool_call_fragments(
    drafts: dict[int, ToolCall], fragments: list
) -> None:
    for fragment in fragments:
        draft = drafts.get(fragment.index)
        if draft is None:
            drafts[fragment.index] = ToolCall(
                id=fragment.id or "",
                name=fragment.function.name or "",
                arguments=fragment.function.arguments or "",
            )
            continue
        # providers may split one tool call across chunks: id/name arrive once,
        # argument JSON arrives as concatenable fragments
        if fragment.id:
            draft.id = fragment.id
        if fragment.function.name:
            draft.name = fragment.function.name
        draft.arguments += fragment.function.arguments or ""


def stream_reply(
    client: Groq,
    messages: list[Message],
    on_chunk: Callable[[str], None],
    tools: list[ToolSchema] | None = None,
) -> Reply:
    request = {"model": MODEL, "messages": messages, "stream": True}
    if tools:
        request["tools"] = tools
    stream = client.chat.completions.create(**request)
    parts: list[str] = []
    usage: Usage | None = None
    drafts: dict[int, ToolCall] = {}
    for chunk in stream:
        if chunk.choices:
            delta = chunk.choices[0].delta
            if delta.content:
                parts.append(delta.content)
                on_chunk(delta.content)
            if delta.tool_calls:
                _merge_tool_call_fragments(drafts, delta.tool_calls)
        # usage arrives only on the final chunk, via Groq's x_groq extension
        if chunk.x_groq and chunk.x_groq.usage:
            usage = Usage(
                prompt_tokens=chunk.x_groq.usage.prompt_tokens,
                completion_tokens=chunk.x_groq.usage.completion_tokens,
                total_time=chunk.x_groq.usage.total_time,
            )
    tool_calls = tuple(drafts[index] for index in sorted(drafts))
    return Reply(text="".join(parts), tool_calls=tool_calls, usage=usage)
