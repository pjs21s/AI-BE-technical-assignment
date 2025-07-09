
from fastapi import FastAPI
from .db import get_db_connection
from .models.candidate import Candidate
from .models.response import InferenceResult
from .services.pipeline import preprocess, retrieve_context, build_prompt, call_llm, postprocess, extract_company_names_from_text
from .exceptions import AppError, http_error_handler, validation_error_handler

app = FastAPI(title="My LLm API", version="0.1.0")

app.add_exception_handler(AppError, http_error_handler)
app.add_exception_handler(Exception, validation_error_handler)

@app.post("/infer", response_model=InferenceResult)
def infer(candidate: Candidate):
    text = preprocess(candidate)
    company_names = extract_company_names_from_text(candidate)
    with get_db_connection() as conn:
        contexts = retrieve_context(text, company_names, conn) or ["(관련 맥락 없음)"]
    if not contexts:
        raise AppError(424, "NO_CONTEXT", "유효한 컨텍스트를 찾지 못했습니다.")
    prompt = build_prompt(candidate, contexts)
    try:
        raw = call_llm(prompt)
    except Exception as e:
        raise AppError(502, "LLM_ERROR", f"LLM 호출 실패: {e}")

    return postprocess(raw)
