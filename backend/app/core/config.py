"""Application settings and environment configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PharmaTrace RAG API"
    API_V1_STR: str = "/api/v1"

    # DeepSeek V4.1 Flash (resmi API model ID: deepseek-flash)
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-flash"

    # Altyapı & Vektör Veritabanı
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "pharmatrace_prospectus"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Retrieval & Guardrail Eşikleri
    MIN_RRF_SCORE: float = 0.25
    TOP_K_RESULTS: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()