import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./prove.db")
    llm_mode: str = os.getenv("LLM_MODE", "mock")
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")


settings = Settings()
