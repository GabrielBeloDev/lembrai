import pytest

from lembrai import observability
from lembrai.cost import Usage

LANGFUSE_ENV_VARS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")


@pytest.fixture
def without_langfuse_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in LANGFUSE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_build_client_is_none_without_keys(without_langfuse_env: None) -> None:
    assert observability._build_client() is None


def test_build_client_is_none_with_only_public_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert observability._build_client() is None


def test_record_turn_is_noop_without_usage(without_langfuse_env: None) -> None:
    assert observability.record_turn("oi", "olá", "llama-3.3-70b-versatile", None) is None


def test_record_turn_is_noop_with_usage(without_langfuse_env: None) -> None:
    usage = Usage(prompt_tokens=10, completion_tokens=5, total_time=0.1)
    assert (
        observability.record_turn("oi", "olá", "llama-3.3-70b-versatile", usage)
        is None
    )


def test_flush_is_noop_without_config(without_langfuse_env: None) -> None:
    assert observability.flush() is None
