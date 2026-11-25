"""Emergency detection and response validation."""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.prompts import GUARDRAIL_CLASSIFIER_PROMPT

OUT_OF_SCOPE_MESSAGE = (
    "Bu sistem yalnızca resmi ilaç prospektüsleri (KÜB/KT) ve farmasötik bilgiler hakkında "
    "soruları yanıtlamak üzere tasarlanmıştır."
)

INSUFFICIENT_CONTEXT_MESSAGE = (
    "Mevcut prospektüs veritabanında bu soruya doğrudan yanıt verecek yeterli klinik bilgi bulunmamaktadır."
)

classifier_llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0.0,
    max_tokens=30,
)


def is_pharmaceutical_query(question: str) -> bool:
    try:
        resp = classifier_llm.invoke(
            [
                SystemMessage(content=GUARDRAIL_CLASSIFIER_PROMPT),
                HumanMessage(content=question),
            ]
        )
        content = resp.content.strip().strip("`").replace("json", "").strip()
        data = json.loads(content)
        return bool(data.get("is_pharmaceutical", False))
    except Exception:
        # Sınıflandırıcı JSON ayrıştırma hatası verirse retrieval + ana system prompt korumasına devret
        return True