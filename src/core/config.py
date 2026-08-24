"""Configuration management module for FInee.ai.

Uses pydantic-settings to load, validate, and manage environment variables
from .env file or system environment with zero hardcoded secrets.
"""

from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Core Application Settings
    APP_NAME: str = Field(
        default="Financial Advisory RAG Platform",
        description="Name of the application",
    )
    APP_ENV: Literal["development", "staging", "production", "testing"] = Field(
        default="development",
        description="Deployment environment",
    )
    APP_HOST: str = Field(
        default="0.0.0.0",
        description="Host address to bind the API server",
    )
    APP_PORT: int = Field(
        default=8000,
        description="Port to bind the API server",
    )

    # Future LLM / Embedding Service Settings (OpenAI-compatible)
    OPENAI_BASE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for OpenAI or OpenAI-compatible LLM endpoint",
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for LLM and Embedding provider",
    )
    CHAT_MODEL: Optional[str] = Field(
        default=None,
        description="Model identifier for financial advisory chat generation",
    )
    EMBED_MODEL: Optional[str] = Field(
        default=None,
        description="Model identifier for document embedding generation",
    )

    # Future Vector Storage / Relational Database (pgvector-ready)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Connection URL for PostgreSQL with pgvector extension",
    )

    # Observability & Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Global application logging level",
    )

    @property
    def is_production(self) -> bool:
        """Check if application is running in production environment."""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if application is running in development environment."""
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()


# Convenient global settings instance
settings = get_settings()
