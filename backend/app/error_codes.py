from enum import Enum
from starlette import status

class Err(Enum):
    NO_CONTEXT = (status.HTTP_424_FAILED_DEPENDENCY, "유효한 컨텍스트 없음")
    LLM_ERROR = (status.HTTP_502_BAD_GATEWAY, "LLM 호출 실패")
    DB_CONN_ERROR = (status.HTTP_500_INTERNAL_SERVER_ERROR, "DB 연결 실패")