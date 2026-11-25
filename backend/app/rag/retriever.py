"""Hybrid retrieval and reranking."""
import unicodedata
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models
from app.core.config import settings


def normalize_tr(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return text.replace("İ", "i").replace("I", "ı").lower().strip()


class PharmaRetriever:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.QDRANT_URL, timeout=30)
        self.dense_model = TextEmbedding(model_name="intfloat/multilingual-e5-large", threads=4)
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25", threads=2)

    def retrieve(
        self,
        query: str,
        top_k: int = settings.TOP_K_RESULTS,
        ilac_filtresi: str | None = None,
        etken_madde_filtresi: str | None = None,
    ) -> list[dict]:
        dense_vec = next(self.dense_model.embed([f"query: {query}"])).tolist()
        sparse_raw = next(self.sparse_model.embed([query]))
        sparse_vec = models.SparseVector(
            indices=sparse_raw.indices.tolist(),
            values=sparse_raw.values.tolist(),
        )

        must_conditions = []
        if ilac_filtresi:
            must_conditions.append(
                models.FieldCondition(key="ilac_adi", match=models.MatchValue(value=ilac_filtresi))
            )
        if etken_madde_filtresi:
            must_conditions.append(
                models.FieldCondition(key="etken_maddeler", match=models.MatchValue(value=etken_madde_filtresi))
            )

        query_filter = models.Filter(must=must_conditions) if must_conditions else None

        points = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            prefetch=[
                models.Prefetch(query=dense_vec, using="dense", limit=20, filter=query_filter),
                models.Prefetch(query=sparse_vec, using="sparse", limit=20, filter=query_filter),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=20,
            with_payload=True,
        ).points

        results: list[dict] = []
        seen_signatures: set[str] = set()

        for pt in points:
            if pt.score < settings.MIN_RRF_SCORE:
                continue
            payload = pt.payload or {}
            raw_text = (payload.get("raw_text") or payload.get("text") or "").strip()
            signature = normalize_tr(raw_text[:160])
            if not signature or signature in seen_signatures:
                continue

            seen_signatures.add(signature)
            results.append(
                {
                    "source_id": len(results) + 1,
                    "ilac_adi": payload.get("ilac_adi", "Bilinmeyen İlaç"),
                    "etken_maddeler": payload.get("etken_maddeler") or [],
                    "dokuman_tipi": payload.get("dokuman_tipi", "KÜB/KT"),
                    "score": round(float(pt.score), 4),
                    "text": raw_text,
                }
            )
            if len(results) >= top_k:
                break

        return results