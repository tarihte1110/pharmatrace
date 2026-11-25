"""Version 1 API router."""
from fastapi import APIRouter
from app.api.v1.endpoints import chat, drugs, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(drugs.router, tags=["Drugs"])