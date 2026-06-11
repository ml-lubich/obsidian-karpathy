from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from env vars.

    Key env vars:
      OKG_VAULT_PATH   - path to the Obsidian vault (overrides CLI arg)
      OKG_HOST         - bind host (default 127.0.0.1; use 0.0.0.0 in Docker)
      OKG_PORT         - bind port (default 8765)
      LLM_BASE_URL     - generic endpoint for ANY OpenAI-compatible LLM
                         (Ollama, LM Studio, Groq, OpenRouter, Mistral, DeepSeek, Gemini compat, ...)
      LLM_MODEL        - generic model ID for that endpoint
      LLM_API_KEY      - generic API key (optional for keyless local endpoints)
      OKG_OPENAI_MODEL - model ID (default gpt-4o-mini)
      OKG_OPENAI_BASE_URL - custom endpoint for local / compatible LLMs
      OPENAI_API_KEY   - standard OpenAI env var (no OKG_ prefix)
      ANTHROPIC_API_KEY - standard Claude API key (auto-uses Claude if set)
      OKG_OPENAI_PREFER - set to 'true' to prefer OpenAI over Claude when both are configured

    Generic LLM_* vars take precedence over provider-specific ones and route through
    the OpenAI-compatible client, so no Anthropic (or OpenAI) account is required.
    """

    vault_path: str = ""
    host: str = "127.0.0.1"
    port: int = 8765

    # OpenAI — OPENAI_API_KEY is the standard var; accept it without prefix too
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Claude / Anthropic
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_prefer: bool = False

    # Explicit provider override ("openai" | "anthropic" | "" for auto-detect)
    llm_provider: str = Field("", alias="LLM_PROVIDER")

    # Generic, provider-agnostic endpoint (any OpenAI-compatible server).
    # Takes precedence over openai_*/anthropic_* settings. Key is optional
    # so keyless local servers (Ollama, LM Studio) work out of the box.
    llm_api_key: str = Field("", alias="LLM_API_KEY")
    llm_base_url: str = Field("", alias="LLM_BASE_URL")
    llm_model: str = Field("", alias="LLM_MODEL")

    model_config = SettingsConfigDict(
      env_file=".env",
      env_file_encoding="utf-8",
        env_prefix="OKG_",
        populate_by_name=True,
        env_ignore_empty=True,
    )

    @property
    def has_generic_llm(self) -> bool:
        """True when a generic OpenAI-compatible endpoint or key is configured."""
        return bool(self.llm_base_url.strip()) or bool(self.llm_api_key.strip())

    @property
    def llm_enabled(self) -> bool:
        return (
            self.has_generic_llm
            or bool(self.openai_api_key.strip())
            or bool(self.anthropic_api_key.strip())
        )

    @property
    def preferred_provider(self) -> str:
        """Return the auto-detected provider based on configured endpoints/keys."""
        if self.has_generic_llm:
            return "openai"
        has_openai = bool(self.openai_api_key.strip())
        has_claude = bool(self.anthropic_api_key.strip())
        if self.openai_prefer and has_openai:
            return "openai"
        if has_claude:
            return "anthropic"
        return "openai"
