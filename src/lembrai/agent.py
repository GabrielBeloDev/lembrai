import json
from collections.abc import Callable

from groq import Groq

from lembrai.chat import Reply, stream_reply
from lembrai.cost import Usage
from lembrai.history import Message
from lembrai.tools import TOOL_SCHEMAS, Toolbox

MAX_TOOL_ROUNDS = 5


def _assistant_message(reply: Reply) -> Message:
    return {
        "role": "assistant",
        "content": reply.text,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": call.arguments},
            }
            for call in reply.tool_calls
        ],
    }


def _parse_arguments(raw_arguments: str) -> dict[str, object] | None:
    try:
        parsed = json.loads(raw_arguments) if raw_arguments.strip() else {}
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def run_agent_turn(
    client: Groq,
    base_messages: list[Message],
    toolbox: Toolbox,
    on_chunk: Callable[[str], None],
    on_tool: Callable[[str, dict[str, object]], None],
    on_malformed_tool: Callable[[str], None],
) -> tuple[str | None, list[Usage]]:
    messages = list(base_messages)
    usages: list[Usage] = []
    for _ in range(MAX_TOOL_ROUNDS):
        reply = stream_reply(client, messages, on_chunk, tools=TOOL_SCHEMAS)
        if reply.usage is not None:
            usages.append(reply.usage)
        if not reply.tool_calls:
            return reply.text, usages
        messages.append(_assistant_message(reply))
        for call in reply.tool_calls:
            arguments = _parse_arguments(call.arguments)
            if arguments is None:
                on_malformed_tool(call.name)
                result = f"Argumentos inválidos para {call.name}: JSON malformado."
            else:
                on_tool(call.name, arguments)
                result = toolbox.execute(call.name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.name,
                    "content": result,
                }
            )
    return None, usages
