from enum import Enum
from http import HTTPStatus
from dataclasses import dataclass

@dataclass(frozen=True)
class ErrorInfo:
    http: HTTPStatus
    default_msg: str

class Err(Enum):
    NO_CONTEXT = ErrorInfo(HTTPStatus.FAILED_DEPENDENCY, "유효한 컨텍스트 없음")
    LLM_ERROR = ErrorInfo(HTTPStatus.BAD_GATEWAY, "LLM 호출 실패")
    DB_CONN_ERROR = ErrorInfo(HTTPStatus.SERVICE_UNAVAILABLE, "DB 연결 실패")