import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai 

load_dotenv()

class Position(BaseModel):
    title: str
    companyName: str
    description: str
    startEndDate: dict
    companyLocation: str

class Candidate(BaseModel):
    firstName: str
    lastName: str
    educations: List[dict]
    positions: List[Position]
    skills: List[str]
    summary: str

class ExperienceTag(BaseModel):
    tag: str
    evidence: str

class InferenceResult(BaseModel):
    tags: List[ExperienceTag]


app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    openai.api_key = os.getenv("OPENAI_API_KEY", "")
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY가 필요합니다.")
    
app = FastAPI(
    title="My LLm API",
    version="0.1.0",
    lifespan=lifespan,
)

def preprocess(candidate: Candidate) -> str:
    edu = candidate.educations[0].get("schoolName", "")
    pos_lines = [f"{p.companyName} - {p.title}: {p.description}"
                 for p in candidate.positions]
    return f"학력: {edu}\n" + "\n".join(pos_lines)

def retrieve_context(text: str) -> List[str]:
    return [
        "연세대학교: 국내 상위권 대학",
        "토스(2016-2019): 스타트업 성장 2배, 조직 2배 확장",
        "네이버 AI(2021-): 대용량 NLP 파이프라인 구축"
    ]

def build_prompt(candidate: Candidate, contexts: List[str]) -> str:
    intro = (
        "지원자 정보와, 관련 경험 리스트가 주어집니다.\n"
        "아래 리스트를 참고해 이 지원자가 가진 경험 태그와 그 증거를\n"
        "JSON 포맷으로 반환해주세요,\n\n"
    )
    ctx_block = "\n".join(f"- {c}" for c in contexts)
    return (
        intro
        + f"지원자 전처리 텍스트:\n{preprocess(candidate)}\n\n"
        + F"경험 리스트:\n{ctx_block}\n\n"
        + "결과:"
    )

def postprocess(llm_output: str) -> InferenceResult:
    try:
        return InferenceResult.model_validate_json(llm_output)
    except Exception as e:
        raise HTTPException(502, detail=f"출력 파싱 실패: {e}")
    
@app.post("/infer", response_model=InferenceResult)
async def infer(candidate: Candidate):
    text = preprocess(candidate)

    contexts = retrieve_context(text)

    prompt = build_prompt(candidate, contexts)

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=512,
        )
        llm_output = response.choices[0].message.content
    except openai.InternalServerError as e:
        raise HTTPException(502, detail=f"LLM 호출 실패: {e}")
    
    return postprocess(llm_output)
