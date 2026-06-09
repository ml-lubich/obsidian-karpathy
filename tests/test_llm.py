import pytest

from obsidian_karpathy.llm import LLMConfig


@pytest.fixture(autouse=True)
def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)


def test_llm_config_is_disabled_without_api_key() -> None:
    assert LLMConfig.from_env().enabled is False


def test_llm_config_uses_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    assert LLMConfig.from_env().enabled is True
