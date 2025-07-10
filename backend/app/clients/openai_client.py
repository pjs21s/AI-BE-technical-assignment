import openai, logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from backend.app.config import settings

log = logging.getLogger(__name__)
openai.api_key = settings.openai_api_key

RETRIABLE = (openai.RateLimitError,
             openai.APIError,
             openai.Timeout,
             TimeoutError)

@retry(
    wait=wait_exponential(
        min=settings.openai_backoff_min,
        max=settings.openai_backoff_max,
        exp_base=2
    ),
    stop=stop_after_attempt(settings.openai_max_retries),
    retry=retry_if_exception_type(RETRIABLE),
    reraise=True,
)
def chat_completion(messages: list[dict], **kw) -> str:
    """LLM 호출 - 재시도·타임아웃 일괄 적용"""
    response = openai.chat.completions.create(
        messages=messages,
        timeout=settings.openai_timeout,
        **kw,
    )
    return response.choices[0].message.content

@retry(
    wait=wait_exponential(
        min=settings.openai_backoff_min,
        max=settings.openai_backoff_max,
        exp_base=2
    ),
    stop=stop_after_attempt(settings.openai_max_retries),
    retry=retry_if_exception_type(RETRIABLE),
    reraise=True,
)
def embedding(input: list[str], model: str, **kw) -> str:
    """LLM 호출 - 재시도·타임아웃 일괄 적용"""
    response = openai.embeddings.create(
        input=input,
        model=model,
        timeout=settings.openai_timeout,
        **kw,
    )
    return response.data[0].embedding
