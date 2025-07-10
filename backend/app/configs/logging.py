import logging

def setup_logging(level: str = "DEBUG") -> None:
    """
    애플리케이션 전역 로깅 포맷/레벨을 초기화합니다.
    여러 모듈에서 logging.basicConfig를 반복 호출하지 않도록
    진입점(main.py)에서 한 번만 실행하세요.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )