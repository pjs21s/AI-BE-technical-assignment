from typing import List

from backend.app.models.candidate import Candidate
from backend.app.clients.openai_client import chat_completion, embedding
from backend.app.exceptions import AppError
from backend.app.error_codes import Err


def preprocess(candidate: Candidate) -> str:
    lines: list[str] = []

    # 학력
    for edu in candidate.educations:
        lines.append(
            f"[EDU] {edu.schoolName} ({edu.degreeName} · {edu.fieldOfStudy})"
        )

    # 경력
    for p in candidate.positions:
        sd = p.startEndDate.get('start', {})
        start = f"{sd['year']}.{sd['month']:02d}"
        ed = p.startEndDate.get('end', {})
        end = f"{ed['year']}.{ed['month']:02d}" if ed else "현재"

        lines.append(
            "[EXP]\n"
            f"  회사(companyName): {p.companyName}\n"
            f"  직책(title): {p.title}\n"
            f"  기간(period): {start}–{end}\n"
            f"  지역(location): {p.companyLocation}\n"
            f"  설명(description): {p.description}"
        )

    # 스킬 / 요약
    if candidate.skills:
        lines.append(f"[SKILLS] {', '.join(candidate.skills)}")
    if candidate.summary:
        lines.append(f"[SUMMARY] {candidate.summary}")

    return "\n".join(lines)


def extract_company_names_from_text(candidate: Candidate) -> list[str]:
    return [p.companyName for p in candidate.positions]


def retrieve_context(text: str,  company_names: list[str], db_conn) -> List[str]:
    query_vector = embedding(input=[text], model="text-embedding-3-small")

    with db_conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT summary_text
            FROM company
            WHERE embedding IS NOT NULL
                AND name = ANY(%s)
            ORDER BY embedding <=> %s::vector
            LIMIT 5;
            """, (company_names, query_vector,)
        )
        summaries = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT title
            FROM company_news
            WHERE company_id IN (
                SELECT id FROM company WHERE name = ANY(%s::text[])
            )
                AND news_date >= CURRENT_DATE - INTERVAL '180 days'
            ORDER BY embedding <=> %s::vector
            LIMIT 10
            """,
            (company_names, query_vector),
        )
        news_titles = [row[0] for row in cursor.fetchall()]
        return summaries + news_titles


_TAG_LIST = [
    "상위권대학교", "대규모 회사 경험", "성장기 스타트업 경험", "리더쉽",
    "대용량 데이터 처리 경험", "IPO", "M&A 경험", "신규 투자 유치 경험",
]

def build_prompt(candidate: Candidate, contexts: list[str]) -> str:
    ctx_block = "\n".join(f"- {c}" for c in contexts) or "(관련 회사 정보 없음)"

    tag_list_block = "\n".join(f"- {t}" for t in _TAG_LIST)

    return f"""
        당신은 HR 분석 전문가입니다. 아래 **지원자 전처리 텍스트**와
        보조 **컨텍스트**(회사·뉴스)를 참고하여 ‘경험 tag–evidence’를 추출하십시오.

        ### 지원자 전처리 텍스트
        {preprocess(candidate)}
        ### 컨텍스트 (회사/뉴스, 최근 180 일)
        {ctx_block}
        ### tag-evidence 규칙
        1. 리더쉽 tag에 대한 evidence는 [EXP] 내 직책(title)을 기반으로 추론하여 활용

        **규칙**
        1. 선택 가능한 태그 ↓  
        {tag_list_block}

        2. **증거(evidence) 문장은 지원자 전처리 텍스트에 존재하는 내용을
        그대로 인용**(필요시 동일 문장 일부만 잘라 사용).  
        - 컨텍스트는 *tag 판단* 참고용이지만, 인용 문장으로 쓰지 마십시오.

        3. 동일 tag가 여러 번 나타나면 **중복 tag를 작성하지 말고**  
        가장 강력한 1~2개 문장을 ‘; ’ 로 연결해 하나의 evidence 로 제시합니다.

        4. 각 evidence 는 최대 60자(번역 시 포함)  
        - 영어 원문만 있으면 한국어 번역 후 인용.

        5. 최종 출력은 **아래 JSON 형식 한 개**만 반환하며,
        불필요한 설명·주석을 포함하지 마십시오.

        ```json
        {{
        "tags": [
            {{ "tag": "상위권대학교", "evidence": "서울대학교 (석사·컴퓨터공학)" }},
            ...
        ]
        }}
        """


def call_llm(prompt: str) -> str:
    try:
        return chat_completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=400,
            presence_penalty=0.2,
            frequency_penalty=0.4
        )
    except Exception as e:
        raise AppError(Err.LLM_ERROR, f"OpenAI 호출 실패: {e}")


def postprocess(raw: str):
    from ..models.response import InferenceResult
    return InferenceResult.model_validate_json(raw)
