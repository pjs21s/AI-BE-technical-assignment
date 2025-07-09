from fastapi import APIRouter
from backend.app.apis.v1 import infer as infer_v1

api_router = APIRouter()
api_router.include_router(infer_v1.router)