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


_TAG_LIST = [
    "상위권대학교", "대규모 회사 경험", "성장기 스타트업 경험", "리더쉽",
    "대용량데이터처리경험", "IPO", "M&A 경험", "신규 투자 유치 경험",
]

def build_prompt(candidate: Candidate, contexts: list[str]) -> str:
    ctx_block = "\n".join(f"- {c}" for c in contexts) or "(관련 회사 정보 없음)"

    return f"""\
            당신은 HR 평가 모델입니다.

            ### 후보 요약
            {preprocess(candidate)}

            ### 관련 회사/조직 정보
            {ctx_block}

            ### 지침
            1. **태그 목록** 중 해당되는 것만 최대 7개까지 골라라.
            2. 태그는 **중복 없이** 한 번만 사용한다.
            3. 각 태그마다 50자 이하의 증거 문장을 제시한다.
            4. 출력은 **JSON 배열**이며, 각 원소는 `"tag"`, `"evidence"` 두 키만 가진다.
            5. 목록에 없는 새로운 태그를 만들지 마라.

            태그 목록: {', '.join(_TAG_LIST)}

            ### 출력 예시
            {{
                "tags": [
                    {{ "tag": "상위권대학교", "evidence": "연세대학교 (학사, 컴퓨터 공학)" }},
                    ...
                ]
            }}

            ### 너의 답변 (위 형식 그대로):
            """


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
