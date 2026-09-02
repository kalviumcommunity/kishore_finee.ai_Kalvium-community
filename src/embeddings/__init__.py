"""Embeddings module for FInee.ai.

Responsible for integrating embedding models, vector generation,
dimension verification, and vector similarity comparisons.
"""

from src.embeddings.embedder import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_VECTOR_DIMENSION,
    EmbeddingConfigurationError,
    EmbeddingError,
    EmbeddingService,
    cosine_similarity,
    embed,
    embed_text,
    embed_texts,
    verify_dimensions,
)

__all__ = [
    "DEFAULT_EMBED_MODEL",
    "DEFAULT_VECTOR_DIMENSION",
    "EmbeddingConfigurationError",
    "EmbeddingError",
    "EmbeddingService",
    "cosine_similarity",
    "embed",
    "embed_text",
    "embed_texts",
    "verify_dimensions",
]
