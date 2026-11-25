"""Request and response schemas for cited interactions."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Kullanıcının ilaç/prospektüs sorusu")
    ilac_filtresi: str | None = Field(default=None, description="Opsiyonel tam ilaç adı filtresi")
    etken_madde_filtresi: str | None = Field(default=None, description="Opsiyonel etken madde filtresi")


class SourceCitation(BaseModel):
    source_id: int
    ilac_adi: str
    etken_maddeler: list[str]
    dokuman_tipi: str
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    is_pharmaceutical: bool
    cached: bool = False