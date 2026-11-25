"""Request validation and rate-limiting helpers."""
import re
from fastapi import Header, HTTPException, status
from app.core.config import settings

# LLM sistem kurallarını atlatmaya veya prompt'u sızdırmaya çalışan yaygın kalıplar
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"forget\s+(everything|all\s+instructions)",
    r"reveal\s+(your\s+)?(system\s+prompt|instructions)",
    r"print\s+(your\s+)?(system\s+prompt|instructions)",
    r"you\s+are\s+now\s+(a|an|in)\s+developer\s+mode",
    r"jailbreak",
    r"önceki\s+(tüm\s+)?(talimatları|kuralları)\s+(unut|yoksay|görmezden\s+gel)",
    r"sistem\s+(mesajını|talimatlarını|promptunu)\s+(yaz|göster|söyle)",
]

COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS]


def sanitize_user_input(text: str) -> str:
    """Kullanıcı girdisini kontrol karakterlerinden temizler ve prompt injection kalıplarını engeller."""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()

    for pattern in COMPILED_PATTERNS:
        if pattern.search(cleaned):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Güvenlik politikası gereği bu istek işlenemez.",
            )

    return cleaned


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """
    .env dosyasında API_ACCESS_KEY tanımlıysa gelen isteklerde X-API-Key başlığını doğrular.
    Boş bırakılmışsa (geliştirme ortamı) tüm isteklere izin verir.
    """
    expected_key = getattr(settings, "API_ACCESS_KEY", None)
    if not expected_key:
        return

    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik API anahtarı.",
        )