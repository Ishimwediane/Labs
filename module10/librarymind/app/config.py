import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for LibraryMind.
    Loads values from environment variables or a .env file.
    """
    # App Settings
    APP_NAME: str = "LibraryMind"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # AI Provider API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Provider Configuration
    PRIMARY_PROVIDER: Literal["openai", "anthropic", "gemini"] = "openai"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    GEMINI_MODEL: str = "gemini-1.5-pro"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vector Database
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "library_docs"

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 3600

    # Rate Limiting & RAG
    RATE_LIMIT_PER_MINUTE: int = Field(60, gt=0)
    RAG_TOP_K: int = 5
    RAG_RELEVANCE_THRESHOLD: float = 0.7
    CHAT_HISTORY_LIMIT: int = 10

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_at_least_one_api_key(self) -> "Settings":
        """Ensure that at least one AI provider API key is configured."""
        if not any([self.OPENAI_API_KEY, self.ANTHROPIC_API_KEY, self.GEMINI_API_KEY]):
            raise ValueError(
                "At least one AI provider API key must be set: "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY"
            )
        return self

    @field_validator("RATE_LIMIT_PER_MINUTE")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        """Double check rate limit is positive (redundant with Field(gt=0) but requested)."""
        if v <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be greater than 0")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a singleton-like cached instance of the Settings.
    """
    return Settings()
