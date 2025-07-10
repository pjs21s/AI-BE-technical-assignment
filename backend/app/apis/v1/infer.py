import json

from fastapi import APIRouter, Body
from pathlib import Path

from backend.app.db import get_db_connection
from backend.app.models.candidate import Candidate
from backend.app.models.response import InferenceResult
from backend.app.services.pipeline import preprocess, retrieve_context, build_prompt, call_llm, postprocess, extract_company_names_from_text
from backend.app.exceptions import AppError
from backend.app.error_codes import Err

router = APIRouter(prefix="/infer", tags=["Inference"])

BASE_DIR = Path(__file__).resolve().parents[2]   # 0: v1, 1: apis, 2: app
EXAMPLE_PATH = BASE_DIR / "examples" / "sample_candidate.json"
sample_candidate = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

@router.post("", response_model=InferenceResult, summary="LLM 태깅 추론")
def infer(candidate: Candidate = Body(example=sample_candidate)):
    text = preprocess(candidate)
    company_names = extract_company_names_from_text(candidate)
    with get_db_connection() as conn:
        contexts = retrieve_context(text, company_names, conn) or ["(관련 맥락 없음)"]
    if not contexts:
        raise AppError(Err.NO_CONTEXT, "유효한 컨텍스트를 찾지 못했습니다.")
    prompt = build_prompt(candidate, contexts)
    try:
        raw = call_llm(prompt)
    except Exception as e:
        raise AppError(Err.LLM_ERROR, f"LLM 호출 실패: {e}")

    return postprocess(raw)