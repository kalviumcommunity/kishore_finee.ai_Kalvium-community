"""Retrieval engine module for finee.ai.

Responsible for semantic similarity search, compliance metadata filtering,
Top-K document chunk retrieval, and reranking.
"""

from src.retrieval.retriever import (
    RetrievalResult,
    compare_k_retrieval,
    retrieve,
)
from src.retrieval.vector_store import (
    InMemoryVectorStore,
    VectorRecord,
)

__all__ = [
    "InMemoryVectorStore",
    "VectorRecord",
    "RetrievalResult",
    "retrieve",
    "compare_k_retrieval",
]
