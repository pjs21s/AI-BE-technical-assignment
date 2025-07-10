# AI Talent-Tagger

이 프로젝트는 지원자(이력 JSON)와 사전에 축적한 회사·뉴스 데이터를 조합해 경험 Tag(예: 상위권대학교, 대규모 회사 경험)와 Evidence(태그를 뒷받침하는 원문 문장)를 추출해 주는 FastAPI 백엔드입니다.

---

## 1. 주요 기능

| 영역 | 내용 |
| :--- | :--- |
| **LLM 파이프라인** | ─ **preprocess**: 지원자 텍스트 생성<br>─ **retrieve_context**: pgvector로 회사 & 최근 180일 내 뉴스 문장 소환<br>─ **build_prompt + call_llm**: `GPT-4o-mini` 호출 → JSON 결과 생성<br>─ **postprocess**: Pydantic 모델로 결과 검증 |
| **DB** | PostgreSQL + pgvector (`company`, `company_news` 테이블) |
| **재시도 / 타임아웃** | `backend/app/clients/openai_client.py` – `tenacity` 기반 공통 래퍼 |
| **API** | `/v1/infer` (POST) : 지원자 JSON → `InferenceResult` |
| **Swagger** | FastAPI 자동 문서, example payload 제공 |
| **테스트** | `pytest` + `TestClient` + `monkeypatch` |

---

## 2. 폴더 구조

```bash
AI-BE-technical-assignment/
├─ backend/
│  ├─ app/
│  │  ├─ apis/                # FastAPI router layer
│  │  │  └─ v1/
│  │  │     └─ infer.py       # /v1/infer endpoint
│  │  ├─ clients/             # 외부 의존(LLM·Redis) 래퍼
│  │  │  ├─ openai_client.py
│  │  │  ├─ redis_client.py
│  │  │  └─ embed_cache.py    # 임베딩 + Redis 캐시
│  │  ├─ configs/             # 환경·로깅
│  │  │  ├─ settings.py
│  │  │  └─ logging.py
│  │  ├─ examples/
│  │  │  └─ sample_candidate.json
│  │  ├─ models/              # Pydantic 모델
│  │  ├─ services/            # 핵심 비즈니스 로직
│  │  │  └─ pipeline.py
│  │  ├─ utils/
│  │  │  └─ profiler.py       # @timed 데코레이터
│  │  ├─ db.py
│  │  ├─ error_codes.py
│  │  ├─ exceptions.py
│  │  └─ main.py              # FastAPI app (entry-point)
│  └─ tests/                  # pytest 스위트
│     ├─ test_config.py
│     └─ sample_candidate.json
├─ nginx/                     # reverse-proxy
├─ postgresql/                # pgvector 볼륨
├─ redis/                     
├─ docker-compose.yaml
├─ Dockerfile
├─ .env                       # 환경변수
└─ pyproject.toml
```

## 3. 빠른 시작

1) 파이썬 3.13 환경

```
poetry install
```

2) .env 수정
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgres://searchright:searchright@localhost/searchright
DB_HOST=localhost
DB_PORT=5432
POSTGRES_USER=searchright
POSTGRES_PASSWORD=searchright
POSTGRES_DB=searchright
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

3) docker compose 사용, 이미지 빌드 및 컨테이너 실행

```
docker compose up --build -d

# 로그 확인
docker compose logs -f redis
docker compose logs -f backend
```

한번에 FastAPI + Nginx + Redis + Postgres 실행이 되도록 작성 완료

4) 사전 데이터 세팅
example_datas 경로로 이동한 상태에서 아래 스크립트를 차례로 실행해 주세요.

```
python ./setup_company_data.py
python ./setup_company_news_data.py
```

5) Swagger

```
서버가 정상적으로 실행되면 아래 주소에서 API 문서를 확인할 수 있습니다.
http://127.0.0.1:8000/docs
```

예시 데이터가 세팅되어 있으므로 별도로 데이터를 넣지 않아도 바로 테스트해볼 수 있습니다.

## 4. 테이블 구조

### `company`

| column        | type            | constraints                 | description                        |
|---------------|-----------------|-----------------------------|------------------------------------|
| id            | SERIAL          | PK                          | 회사 식별자                        |
| name          | TEXT            | UNIQUE                      | 회사명 (예: `네이버`)              |
| data          | JSONB           | –                           | 크롤링·정규화된 원본 JSON          |
| summary_text  | TEXT            | –                           | 회사 요약                 |
| embedding     | VECTOR(1536)    | –                           | pgvector 임베딩 (1536 dim)         |

### `company_news`

| column       | type            | constraints                                   | description                       |
|--------------|-----------------|-----------------------------------------------|-----------------------------------|
| id           | SERIAL          | PK                                            | 뉴스 식별자                       |
| company_id   | INTEGER         | FK → `company(id)` ON DELETE CASCADE          | 소속 회사                         |
| title        | VARCHAR(1000)            | –                                             | 기사 제목                         |
| original_link          | TEXT            | –                                             | 원문 URL                          |
| news_date    | DATE            | –                                             | 기사 날짜 (YYYY-MM-DD)            |
| embedding    | VECTOR(1536)    | –                                             | 제목 임베딩                       |


## 5. API 정의
`POST /v1/infer`

성공 (200) InferenceResult

```json
{
  "tags": [
    {
      "tag": "상위권대학교",
      "evidence": "연세대학교 (학사 · 컴퓨터 공학)"
    },
    ...
  ]
}
```

## 6. 테스트

```
pytest -q
```

## 7. TODO
1. 정교한 성능 측정 및 최적화
2. fine tuning 위한 라벨링 및 평가 시스템 도입
3. 벡터 검색에 대한 인덱스 추가
4. 목표 데이터셋 정확성과 일관성 추가 확보