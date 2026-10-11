from fastapi import APIRouter
from app.api.v1 import history, sentiment, readability

api_v1_router = APIRouter()
api_v1_router.include_router(sentiment.router)
api_v1_router.include_router(readability.router)
api_v1_router.include_router(history.router)
