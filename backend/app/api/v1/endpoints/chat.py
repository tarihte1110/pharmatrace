"""Chat and streaming API endpoints."""
import hashlib
import json
import redis
from fastapi import APIRouter
from app.core.config import settings
from app.rag.graph import pharma_rag_graph
from app.schemas.interaction import ChatRequest, ChatResponse, SourceCitation

router = APIRouter()
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 saat


def _make_cache_key(req: ChatRequest) -> str:
    raw = f"{req.question.strip().lower()}|{req.ilac_filtresi or ''}|{req.etken_madde_filtresi or ''}"
    return "pharmatrace:chat:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/chat", response_model=ChatResponse)
def ask_prospectus(request: ChatRequest) -> ChatResponse:
    cache_key = _make_cache_key(request)
    try:
        cached_payload = redis_client.get(cache_key)
        if cached_payload:
            data = json.loads(cached_payload)
            data["cached"] = True
            return ChatResponse(**data)
    except Exception:
        pass  # Redis kapalıysa akışı bozma

    result = pharma_rag_graph.invoke(
        {
            "question": request.question,
            "ilac_filtresi": request.ilac_filtresi,
            "etken_madde_filtresi": request.etken_madde_filtresi,
            "is_pharmaceutical": True,
            "contexts": [],
            "answer": "",
        }
    )

    citations = [
        SourceCitation(
            source_id=ctx["source_id"],
            ilac_adi=ctx["ilac_adi"],
            etken_maddeler=ctx["etken_maddeler"],
            dokuman_tipi=ctx["dokuman_tipi"],
            score=ctx["score"],
            excerpt=ctx["text"][:280] + ("..." if len(ctx["text"]) > 280 else ""),
        )
        for ctx in result.get("contexts", [])
    ]

    response_obj = ChatResponse(
        answer=result["answer"],
        sources=citations,
        is_pharmaceutical=result["is_pharmaceutical"],
        cached=False,
    )

    try:
        redis_client.setex(cache_key, CACHE_TTL_SECONDS, response_obj.model_dump_json())
    except Exception:
        pass

    return response_obj