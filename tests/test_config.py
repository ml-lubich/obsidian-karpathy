from obsidian_karpathy.config import Settings


def test_settings_enable_llm_when_api_key_exists(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    assert Settings().llm_enabled is True


def test_settings_read_prefixed_vault_path(monkeypatch) -> None:
    monkeypatch.setenv("OKG_VAULT_PATH", "/tmp/demo-vault")

    assert Settings().vault_path == "/tmp/demo-vault"
