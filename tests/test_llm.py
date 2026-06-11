import pytest

from obsidian_knowledge_base import llm
from obsidian_knowledge_base.llm import LLMConfig, chat_with_vault, summarize_markdown


@pytest.fixture(autouse=True)
def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OKG_OPENAI_PREFER", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OKG_OPENAI_BASE_URL", raising=False)


def test_llm_config_is_disabled_without_api_key() -> None:
    assert LLMConfig.from_env().enabled is False


def test_llm_config_uses_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    assert LLMConfig.from_env().enabled is True


def test_summarize_markdown_falls_back_without_llm() -> None:
    cfg = LLMConfig(api_key="", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=False)

    summary = summarize_markdown("# Note\n\nLong form markdown body", "Note", cfg)

    assert "Long form markdown body" in summary


def test_summarize_markdown_uses_model_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LLMConfig(api_key="x", base_url="http://localhost:11434/v1", model="llama", enabled=True, provider="openai")
    monkeypatch.setattr(llm, "_call_llm", lambda _messages, _cfg: "model summary")

    summary = summarize_markdown("# Note\n\nBody", "Note", cfg)

    assert summary == "model summary"


def test_chat_with_vault_rag_mode_uses_retrieved_context(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LLMConfig(api_key="x", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=True, provider="openai")
    captured: dict[str, str] = {}

    def _fake_call(messages: list[dict[str, str]], _cfg: LLMConfig) -> str:
        captured["system"] = messages[0]["content"]
        return "ok"

    graph_data = {
        "nodes": [
            {"id": "n1", "kind": "note", "title": "Graph Explorer", "summary": "Node map", "markdown": "RAG and retrieval"},
            {"id": "n2", "kind": "note", "title": "Writing", "summary": "Publishing loop", "markdown": "editing"},
        ],
        "edges": [],
    }
    monkeypatch.setattr(llm, "_call_llm", _fake_call)

    reply = chat_with_vault(
        [{"role": "user", "content": "how does retrieval graph work"}],
        graph_data,
        cfg,
        mode="rag",
        focus_node_id="n1",
    )

    assert reply == "ok"
    assert "Graph Explorer" in captured["system"]


def test_chat_with_vault_tools_mode_adds_tool_instructions(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LLMConfig(api_key="x", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=True, provider="openai")
    captured: dict[str, str] = {}

    def _fake_call(messages: list[dict[str, str]], _cfg: LLMConfig) -> str:
        captured["system"] = messages[0]["content"]
        return "ok"

    monkeypatch.setattr(llm, "_call_llm", _fake_call)
    chat_with_vault([{"role": "user", "content": "summarize this"}], {"nodes": [], "edges": []}, cfg, mode="tools")

    assert "summarize_node" in captured["system"]


def test_chat_with_vault_requires_enabled_llm() -> None:
    cfg = LLMConfig(api_key="", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=False, provider="openai")

    with pytest.raises(ValueError):
        chat_with_vault([{"role": "user", "content": "hello"}], {"nodes": [], "edges": []}, cfg)


def test_llm_config_detects_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-claude-key")

    cfg = LLMConfig.from_env()

    assert cfg.provider == "anthropic"
    assert cfg.enabled is True
    assert cfg.api_key == "test-claude-key"


def test_llm_config_prefers_openai_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-claude-key")
    monkeypatch.setenv("OKG_OPENAI_PREFER", "true")

    cfg = LLMConfig.from_env()

    assert cfg.provider == "openai"
    assert cfg.enabled is True


def test_summarize_markdown_uses_anthropic_when_provider_set(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LLMConfig(api_key="sk-ant-x", base_url="", model="claude-3-5-haiku-20241022", enabled=True, provider="anthropic")
    monkeypatch.setattr(llm, "_call_anthropic", lambda _msgs, _cfg: "claude summary")

    summary = summarize_markdown("# Note\n\nBody", "Note", cfg)

    assert summary == "claude summary"


def test_llm_provider_explicit_override_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
    monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    cfg = LLMConfig.from_env()

    assert cfg.provider == "openai"
    assert cfg.api_key == "oai-key"


def test_llm_config_enables_keyless_local_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")

    assert LLMConfig.from_env().enabled is True


def test_llm_config_generic_base_url_routes_openai_compatible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")

    assert LLMConfig.from_env().provider == "openai"


def test_llm_config_generic_model_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "llama3.2")

    assert LLMConfig.from_env().model == "llama3.2"


def test_llm_config_generic_key_beats_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
    monkeypatch.setenv("LLM_API_KEY", "generic-key")

    assert LLMConfig.from_env().api_key == "generic-key"


def test_llm_config_generic_endpoint_wins_over_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")

    assert LLMConfig.from_env().provider == "openai"


def test_default_openai_url_without_key_stays_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OKG_OPENAI_BASE_URL", "https://api.openai.com/v1")

    assert LLMConfig.from_env().enabled is False
