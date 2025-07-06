import json
import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture
def sample_candidate():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "sample_candidate.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
    
def test_infer_success(sample_candidate, monkeypatch):
    def fake_create(*args, **kwargs):
        class Choice:
            message = type("M", (), {"content": json.dumps({
                "tags": [
                    {"tag": "상위권대학교", "evidence": "연세대학교"}
                ]
            })})
        return type("R", (), {"choices": [Choice()]})
    monkeypatch.setattr("openai.chat.completions.create", fake_create)

    response = client.post("/infer", json=sample_candidate)
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data["tags"][0]["tag"] == "상위권대학교"

def test_infer_invalid_payload():
    response = client.post("/infer", json={"foo": "bar"})
    assert response.status_code == 422
