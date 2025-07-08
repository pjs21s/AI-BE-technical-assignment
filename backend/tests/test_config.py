import importlib

import backend.app.config as config_module

def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")

    config = importlib.reload(config_module)
    settings = config.settings

    assert settings.openai_api_key == "test-key-123"
    assert settings.database_url == "postgres://user:pass@localhost/db"
