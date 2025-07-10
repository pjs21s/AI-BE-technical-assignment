import importlib
import pytest
from pydantic_core import ValidationError

MODULE_PATH = "backend.app.configs.settings"


def _reload_settings_module():
    """settings 모듈을 새로 로드하고, 그 안의 settings 인스턴스를 반환"""
    mod = importlib.import_module(MODULE_PATH)
    importlib.reload(mod)
    return mod.settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("DATABASE_URL",  "postgres://user:pass@localhost/db")

    settings = _reload_settings_module()

    assert settings.openai_api_key == "test-key-123"
    assert settings.database_url   == "postgres://user:pass@localhost/db"


def test_settings_missing_env_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL",   raising=False)

    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError):
        _reload_settings_module()