import pytest
from types import SimpleNamespace
from backend.app.clients.openai_client import embedding
import backend.app.clients.openai_client as client_mod


def test_embedding_retries_then_succeeds(monkeypatch):
    """앞 두 번은 실패, 세 번째에 성공 → Retry 동작 확인"""
    calls = {"n": 0}

    def fake_embeddings_create(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise client_mod.openai.APIError("temporary", request=None, body=None)
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])

    monkeypatch.setattr(client_mod.openai.embeddings, "create", fake_embeddings_create)

    monkeypatch.setattr("time.sleep", lambda *_: None)

    vec = embedding(input=["foo"], model="text-embedding-3-small")

    assert vec == [0.1, 0.2]
    assert calls["n"] == 3

def test_embedding_retry_exhaust(monkeypatch):
    """모든 시도 실패 → RetryError 발생"""
    def always_fail(*args, **kwargs):
        raise client_mod.openai.APIError("again!", request=None, body=None)

    monkeypatch.setattr(client_mod.openai.embeddings, "create", always_fail)
    monkeypatch.setattr("time.sleep", lambda *_: None)

    with pytest.raises(client_mod.openai.APIError):
        embedding(input=["bar"], model="text-embedding-3-small")
