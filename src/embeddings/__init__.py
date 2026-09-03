"""Embeddings module for FInee.ai.

Responsible for integrating embedding models, vector generation,
batch processing, dimension verification, and vector representation.
"""

from src.embeddings.batch_embedder import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_PRICE_PER_1K_TOKENS,
    BatchEmbedder,
    BatchRunSummary,
    batches,
)
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
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_PRICE_PER_1K_TOKENS",
    "DEFAULT_VECTOR_DIMENSION",
    "BatchEmbedder",
    "BatchRunSummary",
    "EmbeddingAPIError",
    "EmbeddingBatchError",
    "EmbeddingConfigError",
    "EmbeddingError",
    "EmbeddingRecord",
    "EmbeddingService",
    "EmbeddingValidationError",
    "FIneeLangChainEmbeddings",
    "batches",
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

