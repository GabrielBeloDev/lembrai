from lembrai.history import trimmed


def make_history(size: int) -> list[dict[str, str]]:
    return [{"role": "user", "content": f"msg {i}"} for i in range(size)]


def test_short_history_is_returned_unchanged():
    history = make_history(5)
    assert trimmed(history, max_messages=10) == history


def test_long_history_keeps_only_the_most_recent_messages():
    history = make_history(12)
    result = trimmed(history, max_messages=10)
    assert len(result) == 10
    assert result[0]["content"] == "msg 2"
    assert result[-1]["content"] == "msg 11"


def test_history_at_the_limit_is_returned_unchanged():
    history = make_history(10)
    assert trimmed(history, max_messages=10) == history
