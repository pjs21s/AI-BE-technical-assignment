import json
import os
import pytest
import types
from starlette import status

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services import pipeline
from backend.app.clients import openai_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_db(monkeypatch):
    monkeypatch.setattr(pipeline, "retrieve_context", lambda *_a, **_kw: ["(관련 맥락 없음)"])

@pytest.fixture
def sample_candidate():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "sample_candidate.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
    
def test_infer_success(sample_candidate, monkeypatch):
    fake_resp = types.SimpleNamespace(
        choices=[
            types.SimpleNamespace(
                message=types.SimpleNamespace(
                    content=json.dumps(
                        {
                            "tags": [
                                {"tag": "상위권대학교", "evidence": "연세대학교"}
                            ]
                        }
                    )
                )
            )
        ]
    )
    monkeypatch.setattr(openai_client, "chat_completion", lambda **kw: fake_resp)

    response = client.post("/api/infer", json=sample_candidate)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["tags"][0]["tag"] == "상위권대학교"

def test_infer_invalid_payload():
    response = client.post("/api/infer", json={"foo": "bar"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY