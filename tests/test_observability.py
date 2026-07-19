import pytest

from lembrai import observability
from lembrai.cost import Usage

LANGFUSE_ENV_VARS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")
MODEL = "llama-3.3-70b-versatile"


@pytest.fixture(autouse=True)
def reset_client_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    # the client is memoized in module globals; reset before each test
    monkeypatch.setattr(observability, "_initialized", False)
    monkeypatch.setattr(observability, "_client", None)


@pytest.fixture
def without_langfuse_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in LANGFUSE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


class _RaisingClient:
    def start_as_current_observation(self, **_: object) -> object:
        raise RuntimeError("langfuse is down")


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


def test_record_turn_swallows_emission_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(observability, "_get_client", lambda: _RaisingClient())
    usage = Usage(prompt_tokens=10, completion_tokens=5, total_time=0.1)
    assert observability.record_turn("oi", "olá", MODEL, usage) is None


def test_build_updates_with_full_usage():
    usage = Usage(prompt_tokens=10, completion_tokens=5, total_time=0.2)
    updates = observability._build_updates("oi", "olá", MODEL, usage)
    assert updates["model"] == MODEL
    assert updates["input"] == "oi"
    assert updates["output"] == "olá"
    assert updates["usage_details"] == {"input": 10, "output": 5, "total": 15}
    assert "cost_details" in updates
    assert updates["metadata"] == {"total_time_s": 0.2}


def test_build_updates_omits_cost_for_unpriced_model():
    usage = Usage(prompt_tokens=10, completion_tokens=5)
    updates = observability._build_updates("oi", "olá", "unknown-model", usage)
    assert "usage_details" in updates
    assert "cost_details" not in updates


def test_build_updates_omits_metadata_without_total_time():
    updates = observability._build_updates(
        "oi", "olá", MODEL, Usage(prompt_tokens=10, completion_tokens=5)
    )
    assert "metadata" not in updates


def test_build_updates_without_usage_has_only_io_and_model():
    updates = observability._build_updates("oi", "olá", MODEL, None)
    assert set(updates) == {"model", "input", "output"}
