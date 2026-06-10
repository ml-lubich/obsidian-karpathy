from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from env vars.

    Key env vars:
      OKG_VAULT_PATH   - path to the Obsidian vault (overrides CLI arg)
      OKG_HOST         - bind host (default 127.0.0.1; use 0.0.0.0 in Docker)
      OKG_PORT         - bind port (default 8765)
      OKG_OPENAI_MODEL - model ID (default gpt-4o-mini)
      OKG_OPENAI_BASE_URL - custom endpoint for local / compatible LLMs
      OPENAI_API_KEY   - standard OpenAI env var (no OKG_ prefix)
      ANTHROPIC_API_KEY - standard Claude API key (auto-uses Claude if set)
      OKG_OPENAI_PREFER - set to 'true' to prefer OpenAI over Claude when both are configured
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

    model_config = SettingsConfigDict(
      env_file=".env",
      env_file_encoding="utf-8",
        env_prefix="OKG_",
        populate_by_name=True,
        env_ignore_empty=True,
    )

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key.strip()) or bool(self.anthropic_api_key.strip())

    @property
    def preferred_provider(self) -> str:
        """Return 'claude' or 'openai' based on configured keys."""
        has_openai = bool(self.openai_api_key.strip())
        has_claude = bool(self.anthropic_api_key.strip())
        if self.openai_prefer and has_openai:
            return "openai"
        if has_claude:
            return "claude"
        if has_openai:
            return "openai"
        return "openai"
