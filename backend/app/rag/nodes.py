"""RAG graph node implementations."""
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.prompts import PHARMATRACE_SYSTEM_PROMPT
from app.rag.guardrails import (
    INSUFFICIENT_CONTEXT_MESSAGE,
    OUT_OF_SCOPE_MESSAGE,
    is_pharmaceutical_query,
)
from app.rag.retriever import PharmaRetriever


class RAGState(TypedDict):
    question: str
    ilac_filtresi: str | None
    etken_madde_filtresi: str | None
    dokuman_tipi: str | None
    is_pharmaceutical: bool
    contexts: list[dict]
    answer: str


retriever = PharmaRetriever()

generator_llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0.0,
    max_tokens=1400,
)


def guardrail_node(state: RAGState) -> dict:
    allowed = is_pharmaceutical_query(state["question"])
    if not allowed:
        return {"is_pharmaceutical": False, "contexts": [], "answer": OUT_OF_SCOPE_MESSAGE}
    return {"is_pharmaceutical": True}


def retrieve_node(state: RAGState) -> dict:
    docs = retriever.retrieve(
        query=state["question"],
        ilac_filtresi=state.get("ilac_filtresi"),
        etken_madde_filtresi=state.get("etken_madde_filtresi"),
        dokuman_tipi=state.get("dokuman_tipi"),
    )
    return {"contexts": docs}


def generate_node(state: RAGState) -> dict:
    contexts = state.get("contexts", [])
    if not contexts:
        return {"answer": INSUFFICIENT_CONTEXT_MESSAGE}

    blocks = []
    for doc in contexts:
        etken_str = ", ".join(doc["etken_maddeler"]) if doc["etken_maddeler"] else "Belirtilmemiş"
        blocks.append(
            f"<context id='{doc['source_id']}'>\n"
            f"İlaç Adı: {doc['ilac_adi']}\n"
            f"Doküman Tipi: {doc['dokuman_tipi']}\n"
            f"Etken Madde: {etken_str}\n"
            f"İçerik: {doc['text']}\n"
            f"</context>"
        )

    user_message = (
        f"### RETRIEVED PROSPECTUS CONTEXT:\n" + "\n\n".join(blocks) + f"\n\n### USER QUESTION:\n{state['question']}"
    )

    resp = generator_llm.invoke(
        [
            SystemMessage(content=PHARMATRACE_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
    )
    return {"answer": resp.content.strip()}