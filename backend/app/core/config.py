"""Application settings and environment configuration."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PharmaTrace RAG API"
    API_V1_STR: str = "/api/v1"

    # DeepSeek V4.1 Flash (resmi API model ID: deepseek-flash)
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-flash"

    # Altyapı & Vektör Veritabanı
    QDRANT_HOST: str | None = None
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "pharmatrace_prospectus"
    REDIS_HOST: str | None = None
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Retrieval & Guardrail Eşikleri
    MIN_RRF_SCORE: float = 0.25
    TOP_K_RESULTS: int = 6

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def apply_service_hosts(self) -> "Settings":
        if self.QDRANT_HOST:
            self.QDRANT_URL = f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
        if self.REDIS_HOST:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return self


settings = Settings()