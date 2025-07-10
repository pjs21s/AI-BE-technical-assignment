import logging
import time
from functools import wraps
from typing import Callable, TypeVar

_T = TypeVar("_T")

_log = logging.getLogger("prof")      # 전용 로거

def timed(label: str | None = None) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    """
    사용 예:
        from backend.app.utils.profiler import timed

        @timed("retrive_context")
        def retrieve_context(...):
            ...
    """
    def deco(fn: Callable[..., _T]) -> Callable[..., _T]:
        _lbl = label or fn.__name__

        @wraps(fn)
        def wrapper(*args, **kwargs) -> _T:          # type: ignore[override]
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1_000
                _log.debug(f"{_lbl}: {elapsed_ms:.3f} ms")
        return wrapper
    return deco
