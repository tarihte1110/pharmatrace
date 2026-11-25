"""Drug search and cabinet API endpoints."""

from fastapi import APIRouter
from qdrant_client import QdrantClient
from app.core.config import settings

router = APIRouter()


def _load_drug_catalog() -> list[dict[str, str | list[str]]]:
    client = QdrantClient(url=settings.QDRANT_URL, timeout=15)
    catalog: dict[str, dict[str, str | list[str]]] = {}
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            limit=1000,
            offset=offset,
            with_payload=["ilac_adi", "etken_maddeler"],
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            name = payload.get("ilac_adi")
            if not isinstance(name, str) or not name.strip():
                continue

            name = name.strip()
            key = name.casefold()
            entry = catalog.setdefault(key, {"ilac_adi": name, "etken_maddeler": []})
            ingredients = payload.get("etken_maddeler") or []
            if isinstance(ingredients, str):
                ingredients = [ingredients]
            existing_ingredients = entry["etken_maddeler"]
            if isinstance(existing_ingredients, list):
                for ingredient in ingredients:
                    if isinstance(ingredient, str) and ingredient not in existing_ingredients:
                        existing_ingredients.append(ingredient)

        if offset is None:
            break

    return sorted(catalog.values(), key=lambda item: str(item["ilac_adi"]).casefold())


@router.get("/drugs/catalog")
def get_drug_catalog() -> list[dict[str, str | list[str]]]:
    return _load_drug_catalog()


@router.get("/drugs/stats")
def get_drug_stats() -> dict:
    client = QdrantClient(url=settings.QDRANT_URL, timeout=15)
    info = client.get_collection(settings.QDRANT_COLLECTION)
    return {
        "collection": settings.QDRANT_COLLECTION,
        "total_chunks": info.points_count,
        "indexed_fields": list(info.payload_schema.keys()),
    }