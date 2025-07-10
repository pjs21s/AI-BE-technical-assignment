from backend.app.error_codes import Err
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette import status

class AppError(HTTPException):
    def __init__(self, err: Err, message: str | None = None):
        super().__init__(
            status_code=err.value.http,
            detail={"code": err.name,
                    "message": message or err.value.default_msg}
        )

def http_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

def validation_error_handler(request, exc):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"code": "VALIDATION_ERROR", "message": str(exc)})
