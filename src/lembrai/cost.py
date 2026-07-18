from dataclasses import dataclass

# Reference prices in USD per 1M tokens (input, output) from https://groq.com/pricing.
# Groq's free tier charges nothing; these exist to make token cost visible while learning.
PRICES_PER_MILLION: dict[str, tuple[float, float]] = {
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "llama-3.1-8b-instant": (0.05, 0.08),
}


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_time: float | None = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def estimated_cost_usd(model: str, usage: Usage) -> float | None:
    prices = PRICES_PER_MILLION.get(model)
    if prices is None:
        return None
    input_price, output_price = prices
    return (
        usage.prompt_tokens * input_price + usage.completion_tokens * output_price
    ) / 1_000_000


@dataclass
class SessionStats:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    replies: int = 0

    def add_reply(self, usage: Usage | None) -> None:
        self.replies += 1
        if usage is None:
            return
        self.prompt_tokens += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens


def token_breakdown(usage: Usage) -> str:
    return (
        f"{usage.total_tokens} tokens"
        f" ({usage.prompt_tokens} entrada / {usage.completion_tokens} saída)"
    )


def format_usage_line(model: str, usage: Usage) -> str:
    parts = [token_breakdown(usage)]
    cost = estimated_cost_usd(model, usage)
    if cost is not None:
        parts.append(f"~US$ {cost:.6f}")
    if usage.total_time is not None:
        parts.append(f"{usage.total_time:.2f}s")
    return " · ".join(parts)


def format_session_stats(model: str, stats: SessionStats) -> str:
    session_usage = Usage(stats.prompt_tokens, stats.completion_tokens)
    reply_word = "resposta" if stats.replies == 1 else "respostas"
    parts = [f"{stats.replies} {reply_word}", token_breakdown(session_usage)]
    cost = estimated_cost_usd(model, session_usage)
    if cost is not None:
        parts.append(f"~US$ {cost:.6f}")
    return " · ".join(parts)
