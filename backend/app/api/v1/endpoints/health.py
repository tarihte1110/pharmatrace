"""Application and dependency health endpoints."""
from time import sleep

from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    client = QdrantClient(url=settings.QDRANT_URL, timeout=10, check_compatibility=False)
    try:
        info = client.get_collection(settings.QDRANT_COLLECTION)
    except ResponseHandlingException:
        sleep(0.25)
        try:
            info = client.get_collection(settings.QDRANT_COLLECTION)
        except ResponseHandlingException as exc:
            raise HTTPException(status_code=503, detail="Qdrant is unavailable") from exc

    return {
        "status": "ok",
        "model": settings.DEEPSEEK_MODEL,
        "qdrant_collection": settings.QDRANT_COLLECTION,
        "indexed_chunks": info.points_count,
    }