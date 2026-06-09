import pytest

from obsidian_karpathy import llm
from obsidian_karpathy.llm import LLMConfig, chat_with_vault, summarize_markdown


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


def test_summarize_markdown_falls_back_without_llm() -> None:
    cfg = LLMConfig(api_key="", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=False)

    summary = summarize_markdown("# Note\n\nLong form markdown body", "Note", cfg)

    assert "Long form markdown body" in summary


def test_summarize_markdown_uses_model_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LLMConfig(api_key="x", base_url="http://localhost:11434/v1", model="llama", enabled=True)
    monkeypatch.setattr(llm, "_call_openai", lambda _messages, _cfg: "model summary")

    summary = summarize_markdown("# Note\n\nBody", "Note", cfg)

    assert summary == "model summary"


def test_chat_with_vault_rag_mode_uses_retrieved_context(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = LLMConfig(api_key="x", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=True)
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
    monkeypatch.setattr(llm, "_call_openai", _fake_call)

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
    cfg = LLMConfig(api_key="x", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=True)
    captured: dict[str, str] = {}

    def _fake_call(messages: list[dict[str, str]], _cfg: LLMConfig) -> str:
        captured["system"] = messages[0]["content"]
        return "ok"

    monkeypatch.setattr(llm, "_call_openai", _fake_call)
    chat_with_vault([{"role": "user", "content": "summarize this"}], {"nodes": [], "edges": []}, cfg, mode="tools")

    assert "summarize_node" in captured["system"]


def test_chat_with_vault_requires_enabled_llm() -> None:
    cfg = LLMConfig(api_key="", base_url="https://api.openai.com/v1", model="gpt-4o-mini", enabled=False)

    with pytest.raises(ValueError):
        chat_with_vault([{"role": "user", "content": "hello"}], {"nodes": [], "edges": []}, cfg)
