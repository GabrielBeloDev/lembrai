from lembrai.cost import (
    SessionStats,
    Usage,
    estimated_cost_usd,
    format_session_stats,
    format_usage_line,
)

MODEL = "llama-3.3-70b-versatile"


def test_cost_uses_input_and_output_prices():
    usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000)
    assert estimated_cost_usd(MODEL, usage) == 0.59 + 0.79


def test_cost_is_none_for_unknown_model():
    usage = Usage(prompt_tokens=100, completion_tokens=100)
    assert estimated_cost_usd("unknown-model", usage) is None


def test_total_tokens_sums_prompt_and_completion():
    assert Usage(prompt_tokens=7, completion_tokens=3).total_tokens == 10


def test_session_stats_accumulates_replies():
    stats = SessionStats()
    stats.add_reply(MODEL, Usage(prompt_tokens=100, completion_tokens=50))
    stats.add_reply(MODEL, Usage(prompt_tokens=200, completion_tokens=80))
    assert stats.prompt_tokens == 300
    assert stats.completion_tokens == 130
    assert stats.replies == 2
    assert stats.cost_usd > 0


def test_reply_without_usage_still_counts():
    stats = SessionStats()
    stats.add_reply(MODEL, None)
    assert stats.replies == 1
    assert stats.prompt_tokens == 0
    assert stats.cost_usd == 0.0


def test_unpriced_model_accumulates_tokens_but_no_cost():
    stats = SessionStats()
    stats.add_reply("unknown-model", Usage(prompt_tokens=10, completion_tokens=5))
    assert stats.prompt_tokens == 10
    assert stats.cost_usd == 0.0


def test_usage_line_shows_tokens_cost_and_time():
    line = format_usage_line(MODEL, Usage(487, 25, total_time=1.2))
    assert "512 tokens" in line
    assert "487 entrada / 25 saída" in line
    assert "US$" in line
    assert "1.20s" in line


def test_usage_line_omits_cost_for_unknown_model():
    line = format_usage_line("unknown-model", Usage(10, 5))
    assert "US$" not in line


def test_session_stats_formatting_uses_singular_for_one_reply():
    stats = SessionStats()
    stats.add_reply(MODEL, Usage(prompt_tokens=100, completion_tokens=50))
    text = format_session_stats(stats)
    assert "1 resposta ·" in text
    assert "150 tokens" in text


def test_session_stats_formatting_uses_plural():
    stats = SessionStats()
    stats.add_reply(MODEL, Usage(prompt_tokens=10, completion_tokens=5))
    stats.add_reply(MODEL, Usage(prompt_tokens=10, completion_tokens=5))
    assert "2 respostas" in format_session_stats(stats)
