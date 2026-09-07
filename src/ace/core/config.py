"""Application configuration via Pydantic BaseSettings.

All settings are loaded from environment variables (or a .env file).
Import the singleton `settings` object wherever config is needed.
"""
from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the ACE AI service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # Service identity
    # ------------------------------------------------------------------
    app_name: str = Field(default="ACE AI Engine", description="Human-readable service name")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False, description="Enable debug mode (verbose logging)")
    environment: str = Field(default="development", description="development | staging | production")

    # ------------------------------------------------------------------
    # Security — service-to-service auth
    # ------------------------------------------------------------------
    service_api_key: str = Field(
        default="change-me-generate-a-strong-secret",
        description="Secret key required in X-Service-API-Key header from C# backend",
    )

    # ------------------------------------------------------------------
    # Database (PostgreSQL — owned by this AI service)
    # ------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+psycopg2://ace_user:ace_password@localhost:5432/ace_db",
        description="Database connection string, e.g. postgresql+psycopg2://user:pass@host/db",
    )
    db_echo_sql: bool = Field(default=False, description="Log all SQL statements (dev only)")
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=10)

    # ------------------------------------------------------------------
    # LLM (optional — bonus AI enhancements)
    # ------------------------------------------------------------------
    llm_provider: str = Field(default="openai", description="LLM provider: openai | gemini | anthropic")
    llm_model: str = Field(default="gpt-4o-mini", description="Model name passed to LiteLLM")
    llm_api_key: str = Field(default="", description="API key for the chosen LLM provider")
    llm_enabled: bool = Field(default=False, description="Enable LLM-powered enhancements")

    # ------------------------------------------------------------------
    # Embeddings (semantic skill matching)
    # ------------------------------------------------------------------
    embeddings_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model for semantic skill matching",
    )
    embeddings_enabled: bool = Field(default=False, description="Enable semantic skill matching")

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    api_prefix: str = Field(default="/api/v1")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins (C# backend, dev frontend)",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton. Use this everywhere."""
    return Settings()  # type: ignore[call-arg]


# Convenience alias
settings = get_settings()

