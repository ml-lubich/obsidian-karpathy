from __future__ import annotations

from dataclasses import dataclass

from obsidian_karpathy.config import Settings


@dataclass(slots=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    enabled: bool

    @classmethod
    def from_env(cls) -> "LLMConfig":
        cfg = Settings()
        return cls(
            api_key=cfg.openai_api_key,
            base_url=cfg.openai_base_url,
            model=cfg.openai_model,
            enabled=cfg.llm_enabled,
        )


def _build_vault_context(graph_data: dict) -> str:
    lines: list[str] = []
    for node in graph_data.get("nodes", []):
        if node.get("kind") == "note" and len(lines) < 60:
            summary = node.get("summary", "").strip()
            lines.append(f"- **{node['title']}**: {summary}")
    return "\n".join(lines)


def _make_system_prompt(vault_context: str) -> str:
    return (
        "You are an intelligent assistant for an Obsidian-style knowledge base vault. "
        "Help the user understand, navigate, and connect ideas in their vault. "
        "Be concise, insightful, and reference specific notes when relevant.\n\n"
        "Current vault notes:\n"
        f"{vault_context}"
    )


def _call_openai(
    api_messages: list[dict[str, str]],
    config: LLMConfig,
) -> str:
    from openai import OpenAI  # noqa: PLC0415

    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    resp = client.chat.completions.create(model=config.model, messages=api_messages)  # type: ignore[arg-type]
    return resp.choices[0].message.content or ""


def chat_with_vault(
    messages: list[dict[str, str]],
    graph_data: dict,
    config: LLMConfig,
) -> str:
    if not config.enabled:
        raise ValueError("LLM is not configured. Set OPENAI_API_KEY environment variable.")
    system = _make_system_prompt(_build_vault_context(graph_data))
    api_messages: list[dict[str, str]] = [{"role": "system", "content": system}, *messages]
    return _call_openai(api_messages, config)
