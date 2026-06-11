from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from obsidian_knowledge_base.config import Settings


@dataclass(slots=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    enabled: bool
    provider: Literal["openai", "anthropic"] = "openai"

    @classmethod
    def from_env(
        cls,
        api_key_override: str = "",
        base_url_override: str = "",
        model_override: str = "",
        provider_override: str = "",
    ) -> "LLMConfig":
        cfg = Settings()
        provider = _detect_provider(cfg, provider_override)
        api_key = api_key_override or _pick_api_key(cfg, provider)
        base_url = base_url_override or cfg.openai_base_url.strip()
        model = model_override or _pick_model(cfg, provider)
        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            enabled=bool(api_key),
            provider=provider,
        )


def _detect_provider(cfg: Settings, override: str) -> Literal["openai", "anthropic"]:
    if override in ("openai", "anthropic"):
        return override  # type: ignore[return-value]
    explicit = cfg.llm_provider.strip()
    if explicit in ("openai", "anthropic"):
        return explicit  # type: ignore[return-value]
    return cfg.preferred_provider  # type: ignore[return-value]


def _pick_api_key(cfg: Settings, provider: Literal["openai", "anthropic"]) -> str:
    if provider == "anthropic":
        return cfg.anthropic_api_key.strip()
    return cfg.openai_api_key.strip()


def _pick_model(cfg: Settings, provider: Literal["openai", "anthropic"]) -> str:
    if provider == "anthropic":
        return cfg.anthropic_model.strip() or "claude-3-5-sonnet-20241022"
    return cfg.openai_model.strip() or "gpt-4o-mini"


def _build_vault_context(graph_data: dict) -> str:
    lines: list[str] = []
    for node in graph_data.get("nodes", []):
        if node.get("kind") == "note" and len(lines) < 60:
            summary = node.get("summary", "").strip()
            lines.append(f"- **{node['title']}**: {summary}")
    return "\n".join(lines)


def _note_rows(graph_data: dict) -> list[dict[str, str]]:
    return [node for node in graph_data.get("nodes", []) if node.get("kind") == "note"]


def _fallback_summary(markdown: str, limit: int = 220) -> str:
    cleaned = " ".join(line.strip() for line in markdown.splitlines() if line.strip())
    return cleaned[:limit].rstrip() or "No markdown content available."


def _node_text(node: dict[str, str]) -> str:
    tags = " ".join(node.get("tags", []))
    return " ".join(
        [
            node.get("title", ""),
            node.get("summary", ""),
            node.get("markdown", "")[:800],
            tags,
        ]
    ).lower()


def _query_terms(query: str) -> list[str]:
    return [term for term in query.lower().split() if len(term) >= 3]


def _score_note(node: dict[str, str], terms: list[str], focus_node_id: str) -> int:
    score = 0
    haystack = _node_text(node)
    for term in terms:
        score += haystack.count(term)
    if focus_node_id and node.get("id") == focus_node_id:
        score += 6
    return score


def _rag_context(query: str, graph_data: dict, focus_node_id: str, limit: int = 8) -> str:
    terms = _query_terms(query)
    notes = _note_rows(graph_data)
    ranked = sorted(notes, key=lambda node: _score_note(node, terms, focus_node_id), reverse=True)
    picked = [node for node in ranked if _score_note(node, terms, focus_node_id) > 0][:limit]
    if not picked:
        picked = notes[: min(limit, len(notes))]
    rows = [f"- **{node['title']}** ({node.get('path', '')}): {node.get('summary', '')}" for node in picked]
    return "\n".join(rows)


def _make_system_prompt(vault_context: str) -> str:
    return (
        "You are an intelligent assistant for an Obsidian-style knowledge base vault. "
        "Help the user understand, navigate, and connect ideas in their vault. "
        "Be concise, insightful, and reference specific notes when relevant.\n\n"
        "Current vault notes:\n"
        f"{vault_context}"
    )


def _tools_prompt(graph_data: dict, focus_node_id: str) -> str:
    node_count = len(graph_data.get("nodes", []))
    edge_count = len(graph_data.get("edges", []))
    focus = focus_node_id or "none"
    return (
        "You are in tools mode. Use concise action-oriented answers and propose concrete next steps. "
        "You can call these conceptual tools: summarize_node(node_id), suggest_prune_candidates(), "
        "find_related_nodes(node_id). Mention which tool you used in plain English.\n\n"
        f"Graph stats: nodes={node_count}, edges={edge_count}, focus_node_id={focus}."
    )


def _call_openai(
    api_messages: list[dict[str, str]],
    config: LLMConfig,
) -> str:
    from openai import OpenAI  # noqa: PLC0415

    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    resp = client.chat.completions.create(model=config.model, messages=api_messages)  # type: ignore[arg-type]
    return resp.choices[0].message.content or ""


def _call_anthropic(
    api_messages: list[dict[str, str]],
    config: LLMConfig,
) -> str:
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=config.api_key)
    system = ""
    user_messages = []
    for msg in api_messages:
        if msg["role"] == "system":
            system = msg["content"]
        else:
            user_messages.append(msg)
    resp = client.messages.create(
        model=config.model,
        max_tokens=1024,
        system=system or "You are a helpful assistant.",
        messages=user_messages,  # type: ignore[arg-type]
    )
    return resp.content[0].text if resp.content else ""


def _call_llm(
    api_messages: list[dict[str, str]],
    config: LLMConfig,
) -> str:
    """Dispatch to the appropriate LLM provider."""
    if config.provider == "anthropic":
        return _call_anthropic(api_messages, config)
    return _call_openai(api_messages, config)


def summarize_markdown(markdown: str, title: str, config: LLMConfig) -> str:
    if not config.enabled:
        return _fallback_summary(markdown)
    prompt = (
        "Summarize this Obsidian note in 3 crisp bullet points and one short takeaway sentence.\n\n"
        f"Title: {title}\n\n"
        f"Markdown:\n{markdown[:6000]}"
    )
    api_messages = [{"role": "user", "content": prompt}]
    return _call_llm(api_messages, config) or _fallback_summary(markdown)


def _context_for_mode(
    mode: Literal["basic", "rag", "tools"],
    graph_data: dict,
    focus_node_id: str,
    user_text: str,
) -> str:
    if mode == "tools":
        return _tools_prompt(graph_data, focus_node_id)
    if mode == "rag":
        return _rag_context(user_text, graph_data, focus_node_id)
    return _build_vault_context(graph_data)


def chat_with_vault(
    messages: list[dict[str, str]],
    graph_data: dict,
    config: LLMConfig,
    mode: Literal["basic", "rag", "tools"] = "rag",
    focus_node_id: str = "",
) -> str:
    if not config.enabled:
        raise ValueError("LLM is not configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
    user_text = messages[-1]["content"] if messages else ""
    context = _context_for_mode(mode, graph_data, focus_node_id, user_text)
    system = _make_system_prompt(context)
    api_messages: list[dict[str, str]] = [{"role": "system", "content": system}, *messages]
    return _call_llm(api_messages, config)


def propose_summarization_jobs(graph_data: dict, limit: int = 12) -> list[dict[str, object]]:
    notes = _note_rows(graph_data)
    ranked = sorted(notes, key=lambda node: int(node.get("markdown_length", 0)), reverse=True)
    jobs: list[dict[str, object]] = []
    for index, node in enumerate(ranked[:limit]):
        jobs.append(
            {
                "node_id": node.get("id", ""),
                "title": node.get("title", "Untitled"),
                "reason": "Large markdown body; strong candidate for compression.",
                "priority": index + 1,
            }
        )
    return jobs


def propose_pruning_jobs(graph_data: dict, limit: int = 12) -> list[dict[str, object]]:
    missing = [node for node in graph_data.get("nodes", []) if node.get("kind") == "missing"]
    notes = _note_rows(graph_data)
    isolated = [
        node
        for node in notes
        if int(node.get("backlinks", 0)) == 0 and int(node.get("outlinks", 0)) == 0
    ]
    candidates = missing + isolated
    jobs: list[dict[str, object]] = []
    for index, node in enumerate(candidates[:limit]):
        jobs.append(
            {
                "node_id": node.get("id", ""),
                "title": node.get("title", "Untitled"),
                "reason": "Missing-target or isolated node; consider pruning/merging.",
                "priority": index + 1,
            }
        )
    return jobs
