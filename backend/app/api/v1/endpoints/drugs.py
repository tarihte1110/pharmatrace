"""Drug search and cabinet API endpoints."""
from fastapi import APIRouter
from qdrant_client import QdrantClient
from app.core.config import settings

router = APIRouter()


@router.get("/drugs/stats")
def get_drug_stats() -> dict:
    client = QdrantClient(url=settings.QDRANT_URL, timeout=15)
    info = client.get_collection(settings.QDRANT_COLLECTION)
    return {
        "collection": settings.QDRANT_COLLECTION,
        "total_chunks": info.points_count,
        "indexed_fields": list(info.payload_schema.keys()),
    }