
from fastapi import FastAPI
from backend.app.db import get_db_connection
from backend.app.models.candidate import Candidate
from backend.app.models.response import InferenceResult
from backend.app.services.pipeline import preprocess, retrieve_context, build_prompt, call_llm, postprocess, extract_company_names_from_text
from backend.app.exceptions import AppError, http_error_handler, validation_error_handler
from backend.app.error_codes import Err

app = FastAPI(title="My LLM API", version="0.1.0")

app.add_exception_handler(AppError, http_error_handler)
app.add_exception_handler(Exception, validation_error_handler)

@app.post("/infer", response_model=InferenceResult)
def infer(candidate: Candidate):
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
