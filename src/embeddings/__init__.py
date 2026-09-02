"""Embeddings module for FInee.ai.

Responsible for integrating embedding models, vector generation,
batch processing, dimension verification, and vector representation.
"""

from src.embeddings.embedder import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_VECTOR_DIMENSION,
    FIneeLangChainEmbeddings,
    cosine_similarity,
    embed,
    embed_texts,
    get_langchain_embeddings,
    verify_dimensions,
)
from src.embeddings.embedding_service import (
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingAPIError,
    EmbeddingBatchError,
    EmbeddingConfigError,
    EmbeddingError,
    EmbeddingRecord,
    EmbeddingService,
    EmbeddingValidationError,
    embed_chunks,
    embed_query,
    embed_text,
    get_embedding_service,
)

__all__ = [
    "DEFAULT_EMBED_MODEL",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_EMBEDDING_BATCH_SIZE",
    "DEFAULT_VECTOR_DIMENSION",
    "EmbeddingAPIError",
    "EmbeddingBatchError",
    "EmbeddingConfigError",
    "EmbeddingError",
    "EmbeddingRecord",
    "EmbeddingService",
    "EmbeddingValidationError",
    "FIneeLangChainEmbeddings",
    "cosine_similarity",
    "embed",
    "embed_chunks",
    "embed_query",
    "embed_text",
    "embed_texts",
    "get_embedding_service",
    "get_langchain_embeddings",
    "verify_dimensions",
]
