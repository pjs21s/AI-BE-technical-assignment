from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
    

def http_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

def validation_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"code": "VALIDATION_ERROR", "message": str(exc)})
