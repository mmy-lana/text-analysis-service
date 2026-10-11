from fastapi import APIRouter
from app.api.v1 import sentiment, readability

api_v1_router = APIRouter()
api_v1_router.include_router(sentiment.router)
api_v1_router.include_router(readability.router)
