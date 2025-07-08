from typing import List
import openai
from ..config import settings

openai.api_key = settings.openai_api_key

from ..models.candidate import Candidate


def preprocess(candidate: Candidate) -> str:
    lines = []

    # 1. 헤드라인/요약
    if candidate.headline:
        lines.append(f"헤드라인: {candidate.headline}")
    if candidate.summary:
        lines.append(f"요약: {candidate.summary}")

    # 2. 학력
    edu = candidate.educations[0]
    school = edu.schoolName or ""
    degree = edu.degreeName or ""
    field = edu.fieldOfStudy or ""
    if school:
        lines.append(f"학력: {school} ({degree}, {field})")

    # 3. 주요 스킬
    if candidate.skills:
        skills = ", ".join(candidate.skills)
        lines.append(f"주요 스킬: {skills}")

    # 4. 포지션별 상세 이력
    for p in candidate.positions:
        # 기간
        sd = p.startEndDate.get("start", {})
        ed = p.startEndDate.get("end", {})
        start = f"{sd.get('year')}-{sd.get('month'):02d}" if sd else "?"
        end = f"{ed.get('year')}-{ed.get('month'):02d}" if ed else "현재"
        # 회사/직무/지역/팀 규모 키워드
        desc = p.description.replace("\n", " ")  # 한 줄로
        lines.append(
            f"[{start} ~ {end}] {p.companyName} - {p.title} @ {p.companyLocation}\n"
            f"  설명: {desc}"
        )

    return "\n".join(lines)


def retrieve_context(text: str, db_conn) -> List[str]:
    with db_conn.cursor() as cursor:
        embedding_response = openai.embeddings.create(input=[text], model="text-embedding-3-small")
        query_vector = embedding_response.data[0].embedding

        cursor.execute(
            """
            SELECT summary_text
            FROM company
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5;
            """, (query_vector,)
        )
        return [row[0] for row in cursor.fetchall()]


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


def call_llm(prompt: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512,
    )
    return response.choices[0].message.content


def postprocess(raw: str):
    from ..models.response import InferenceResult
    return InferenceResult.model_validate_json(raw)
