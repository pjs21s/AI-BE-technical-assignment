import json
import pathlib
import pytest

from backend.app.services import pipeline


@pytest.fixture()
def sample_candidate():
    here = pathlib.Path(__file__).parent
    with open(here / "sample_candidate.json", encoding="utf-8") as f:
        return json.load(f)


def test_preprocess_format(sample_candidate):
    cand_obj = pipeline.Candidate.model_validate(sample_candidate)
    text = pipeline.preprocess(cand_obj)

    assert "[EDU]" in text
    assert "[EXP]" in text
    assert sample_candidate["educations"][0]["schoolName"] in text


def test_extract_company_names(sample_candidate):
    cand_obj = pipeline.Candidate.model_validate(sample_candidate)
    names = pipeline.extract_company_names_from_text(cand_obj)
    expected = [p["companyName"] for p in sample_candidate["positions"]]
    assert names == expected


class FakeCursor:
    def __init__(self):
        self._queues = [
            [("요약1",), ("요약2",)],
            [("뉴스1",), ("뉴스2",)],
        ]
    def execute(self, *_a, **_kw):
        pass
    def fetchall(self):
        return self._queues.pop(0)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass


class FakeConn:
    def cursor(self):
        return FakeCursor()

def test_retrieve_context(monkeypatch, sample_candidate):
    monkeypatch.setattr(
        "backend.app.services.pipeline.get_cached_embedding",
        lambda *a, **kw: [0.1, 0.2]
    )
    cand_obj = pipeline.Candidate.model_validate(sample_candidate)
    txt = pipeline.preprocess(cand_obj)
    ctx = pipeline.retrieve_context(
        txt,
        ["네이버", "토스"],
        FakeConn()
    )
    assert ctx == ["요약1", "요약2", "뉴스1", "뉴스2"]


def test_build_prompt_contains_sections(sample_candidate):
    cand_obj = pipeline.Candidate.model_validate(sample_candidate)
    pr = pipeline.build_prompt(cand_obj, ["컨텍스트1"])

    assert "지원자 전처리 텍스트" in pr
    assert "컨텍스트" in pr
    # 태그 목록의 임의 항목이 문자열로 포함되는지
    assert "상위권대학교" in pr


def test_call_llm_returns_content(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "chat_completion",
        lambda **kwargs: "OK",
    )
    assert pipeline.call_llm("any prompt") == "OK"
