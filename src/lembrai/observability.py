from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from lembrai.cost import Usage, estimated_cost_usd

if TYPE_CHECKING:
    from langfuse import Langfuse

logger = logging.getLogger(__name__)

_initialized = False
_client: Langfuse | None = None


def _build_client() -> Langfuse | None:
    keys_present = bool(
        os.environ.get("LANGFUSE_PUBLIC_KEY")
        and os.environ.get("LANGFUSE_SECRET_KEY")
    )
    if not keys_present:
        return None
    try:
        from langfuse import Langfuse
    except ImportError:
        return None
    return Langfuse()


def _get_client() -> Langfuse | None:
    global _initialized, _client
    if not _initialized:
        _client = _build_client()
        _initialized = True
    return _client


def _build_updates(
    user_input: str, reply: str, model: str, usage: Usage | None
) -> dict[str, object]:
    updates: dict[str, object] = {
        "model": model,
        "input": user_input,
        "output": reply,
    }
    if usage is not None:
        updates["usage_details"] = {
            "input": usage.prompt_tokens,
            "output": usage.completion_tokens,
            "total": usage.total_tokens,
        }
        cost = estimated_cost_usd(model, usage)
        if cost is not None:
            updates["cost_details"] = {"total": cost}
        if usage.total_time is not None:
            # the turn's real latency lives here: the generation is emitted after
            # the turn finishes, so Langfuse's native span duration is ~0
            updates["metadata"] = {"total_time_s": usage.total_time}
    return updates


def _emit_generation(
    client: Langfuse, user_input: str, reply: str, updates: dict[str, object]
) -> None:
    with client.start_as_current_observation(
        name="chat_turn", as_type="generation"
    ) as generation:
        generation.update(**updates)
        client.set_current_trace_io(input=user_input, output=reply)


def record_turn(
    user_input: str, reply: str, model: str, usage: Usage | None
) -> None:
    client = _get_client()
    if client is None:
        return
    # build the payload outside the best-effort guard so our own bugs error loud
    updates = _build_updates(user_input, reply, model, usage)
    try:
        _emit_generation(client, user_input, reply, updates)
    except Exception:
        # a failing trace must never break the chat turn — tracing is best-effort
        logger.debug("langfuse trace failed", exc_info=True)


def flush() -> None:
    client = _get_client()
    if client is not None:
        client.flush()
