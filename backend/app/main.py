from fastapi import FastAPI
from backend.app.apis import api_router
from backend.app.exceptions import AppError, http_error_handler, validation_error_handler
from contextlib import asynccontextmanager
from backend.app.clients.redis_client import rds
from backend.app.configs import settings, setup_logging

setup_logging(level=settings.log_level if hasattr(settings, "log_level") else "DEBUG")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        rds.close()

app = FastAPI(title="My LLM API", version="0.1.0", lifespan=lifespan)

app.add_exception_handler(AppError, http_error_handler)
app.add_exception_handler(Exception, validation_error_handler)

app.include_router(api_router, prefix="/api")
