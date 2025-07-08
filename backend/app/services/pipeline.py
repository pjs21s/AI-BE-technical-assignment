from typing import List
import openai
from ..config import settings

openai.api_key = settings.openai_api_key

from ..models.candidate import Candidate


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
    query_vector = openai.embeddings.create(
        input=[text], model="text-embedding-3-small"
    ).data[0].embedding

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
    "대용량데이터처리경험", "IPO", "M&A 경험", "신규 투자 유치 경험",
]

def build_prompt(candidate: Candidate, contexts: list[str]) -> str:
    ctx_block = "\n".join(f"- {c}" for c in contexts) or "(관련 회사 정보 없음)"

    return f"""\
            당신은 다음 JSON 파싱 결과(아래 '지원자 전처리 텍스트')를 읽고,
            미리 정의된 경험 태그를 선택해 evidence 와 함께 반환합니다.

            전처리 텍스트 규칙
            [EDU] …          → 학력
            [EXP] …          → 경력
            └ companyName / title / period / location / description
            [SKILLS] …       → 보유 스킬
            [SUMMARY] …      → 이력 요약

            증거(evidence)는 가능하면 description 안의 구체적 문구(투자 금액·M&A·조직 10→45명 등)를 그대로 포함하십시오.

            ### 후보 요약
            {preprocess(candidate)}

            ### 관련 회사/조직 정보/최근 180일 뉴스 정보
            {ctx_block}

            ### 지침
            1. **_TAG_LIST** 중 해당되는 것만 최대 7개까지 골라라.
            2. tag는 **중복 없이** 한 번만 사용한다.
            3. 각 tag마다 50자 이하의 evidence 문장을 제시한다.
            4. 출력은 **JSON 배열**이며, 각 원소는 `"tag"`, `"evidence"` 두 키만 가진다.

            태그 목록: {', '.join(_TAG_LIST)}

            ### 출력 예시
            {{
                "tags": [
                    {{ "tag": "상위권대학교", "evidence": "연세대학교 (학사, 컴퓨터 공학)" }},
                    ...
                ]
            }}

            ### 반환 규칙
            - "tag": 미리 정의된 태그 중 하나
            - "evidence": 해당 태그를 뒷받침하는 가장 핵심적인 한 문장
                · 예) "토스 시리즈 F 2,060억 투자 유치 지원"
                · 같은 태그가 여러 회사에서 관찰되면 '; '로 구분
            - 동일 태그가 중복되지 않도록 합니다.
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
