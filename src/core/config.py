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

    # Groq API Settings (OpenAI-compatible)
    GROQ_BASE_URL: Optional[str] = Field(
        default="https://api.groq.com/openai/v1",
        description="Base URL for Groq API endpoint",
    )
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for Groq LLM provider",
    )

    # OpenAI-compatible LLM / Embedding Service Settings
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
        description="Legacy model identifier for document embedding generation",
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Model identifier for document and query embeddings",
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=50,
        description="Default batch size for embedding generation requests",
    )
    EMBEDDING_DIMENSIONS: Optional[int] = Field(
        default=None,
        description="Optional vector dimension override for embedding model",
    )

    # Vector Storage Settings
    VECTOR_DB_TYPE: str = Field(
        default="chroma",
        description="Vector database engine type (e.g. chroma, memory)",
    )
    VECTOR_COLLECTION_NAME: str = Field(
        default="rag_chunks",
        description="Default collection name for chunk vector embeddings",
    )
    VECTOR_DIMENSION: int = Field(
        default=1536,
        description="Expected embedding vector dimension",
    )
    VECTOR_DISTANCE_METRIC: str = Field(
        default="cosine",
        description="Distance metric for vector similarity (e.g. cosine, l2, ip)",
    )
    VECTOR_DB_PATH: str = Field(
        default="./data/vector_db",
        description="Local directory path for vector database persistence",
    )
    CHROMA_TENANT: Optional[str] = Field(
        default=None,
        description="Optional Chroma tenant ID for cloud/multi-tenant setup",
    )
    CHROMA_DATABASE: Optional[str] = Field(
        default=None,
        description="Optional Chroma database name",
    )
    DATABASE_API_KEY: Optional[str] = Field(
        default=None,
        description="Optional API key for managed vector or relational database",
    )

    # Relational Database / PostgreSQL (pgvector-ready)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Connection URL for PostgreSQL with pgvector extension",
    )



    # LLM Generation & Output Control Settings
    LLM_TEMPERATURE: float = Field(
        default=0.1,
        description="Controls randomness of the LLM generation",
    )
    LLM_MAX_TOKENS: int = Field(
        default=500,
        description="Maximum output tokens for the LLM",
    )
    LLM_TOP_P: float = Field(
        default=1.0,
        description="Top-p sampling parameter",
    )
    LLM_STOP_SEQUENCES: Optional[str] = Field(
        default=None,
        description="Optional comma-separated list of stop sequences",
    )

    # Re-ranking Retrieval Settings
    RERANK_ENABLED: bool = Field(
        default=True,
        description="Toggle to enable or bypass re-ranking of retrieved candidates",
    )
    RERANK_CANDIDATE_K: int = Field(
        default=10,
        description="Number of initial candidates to retrieve from vector store before re-ranking",
    )
    RERANK_FINAL_K: int = Field(
        default=3,
        description="Number of final top-k candidates to return after re-ranking",
    )
    RERANK_MODEL: Optional[str] = Field(
        default=None,
        description="Model identifier used for re-ranking scoring (defaults to CHAT_MODEL)",
    )
    RERANK_TIMEOUT_SECONDS: float = Field(
        default=5.0,
        description="Timeout in seconds for re-ranking scoring calls",
    )

    # Context Injection & Token Budget Settings
    MAX_MODEL_CONTEXT_TOKENS: int = Field(
        default=8192,
        description="Total context window limit of the model (e.g., 8192, 128000)",
    )
    MAX_CONTEXT_TOKENS: int = Field(
        default=5000,
        description="Maximum tokens allocated for injected retrieved context",
    )
    RESERVED_ANSWER_TOKENS: int = Field(
        default=1500,
        description="Reserved token budget for model answer completion",
    )
    RESERVED_INSTRUCTION_TOKENS: int = Field(
        default=800,
        description="Reserved token budget for system instructions and user question",
    )

    # Retrieval Guardrails & Safe Refusal Settings
    MIN_TOP_SCORE: float = Field(
        default=0.72,
        description="Minimum relevance/similarity score required for top retrieved chunk",
    )
    MIN_SUPPORTING_CHUNKS: int = Field(
        default=1,
        description="Minimum number of retrieved chunks meeting the MIN_TOP_SCORE threshold",
    )
    RETRIEVAL_TOP_K: int = Field(
        default=4,
        description="Default number of chunks retrieved for guardrail evaluation",
    )
    SAFE_REFUSAL_MESSAGE: str = Field(
        default="I don't have enough reliable evidence in the approved knowledge base to answer that question.",
        description="Standardized compliance refusal text returned when retrieval evidence is insufficient",
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

    @property
    def parsed_stop_sequences(self) -> Optional[list[str]]:
        """Parse LLM_STOP_SEQUENCES from comma-separated string to list of strings."""
        if not self.LLM_STOP_SEQUENCES:
            return None
        seqs = [s.strip() for s in self.LLM_STOP_SEQUENCES.split(",") if s.strip()]
        return seqs if seqs else None


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()


# Convenient global settings instance
settings = get_settings()
