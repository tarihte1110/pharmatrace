"""Application and dependency health endpoints."""
from fastapi import APIRouter
from qdrant_client import QdrantClient
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    client = QdrantClient(url=settings.QDRANT_URL, timeout=10)
    info = client.get_collection(settings.QDRANT_COLLECTION)
    return {
        "status": "ok",
        "model": settings.DEEPSEEK_MODEL,
        "qdrant_collection": settings.QDRANT_COLLECTION,
        "indexed_chunks": info.points_count,
    }