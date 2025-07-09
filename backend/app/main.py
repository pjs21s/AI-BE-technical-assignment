from fastapi import FastAPI
from backend.app.apis import api_router
from backend.app.exceptions import AppError, http_error_handler, validation_error_handler


app = FastAPI(title="My LLM API", version="0.1.0")

app.add_exception_handler(AppError, http_error_handler)
app.add_exception_handler(Exception, validation_error_handler)

app.include_router(api_router, prefix="/api")
