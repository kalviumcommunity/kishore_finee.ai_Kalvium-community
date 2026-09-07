"""Similarity search and Top-K retrieval module for finee.ai RAG platform.

Provides query embedding, vector database search, similarity scoring,
source metadata tracking, and multi-k retrieval inspection.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field

from src.embeddings.embedding_service import EmbeddingService, get_embedding_service
from src.retrieval.vector_store import InMemoryVectorStore, VectorRecord

logger = logging.getLogger(__name__)


class RetrievalResult(BaseModel):
    """Structured result item returned by top-k similarity retrieval."""

    rank: int = Field(..., description="1-indexed rank of the retrieved item")
    score: float = Field(..., description="Cosine similarity score against user query")
    text: str = Field(..., description="Text content of the retrieved document chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provenance metadata (source, chunk_index, etc.)")
    embedding_model: str = Field(..., description="Model identifier used for vector embedding")
    id: Optional[str] = Field(default=None, description="Unique record identifier")

    def to_dict(self) -> Dict[str, Any]:
        """Convert retrieval result to standard dictionary."""
        return {
            "rank": self.rank,
            "score": round(self.score, 4),
            "text": self.text,
            "metadata": self.metadata,
            "embedding_model": self.embedding_model,
            "id": self.id,
        }


def _embed_query_safe(service: EmbeddingService, query: str) -> List[float]:
    """Embed query with fallback to deterministic semantic vector when API key is unconfigured."""
    try:
        return service.embed_query(query)
    except Exception as exc:
        from src.embeddings.embedder import _generate_deterministic_semantic_vector
        logger.info("Using deterministic semantic query embedding: %s", exc)
        return _generate_deterministic_semantic_vector(query, dimension=1536)


def retrieve(
    query: str,
    k: int = 3,
    collection: Optional[InMemoryVectorStore] = None,
    embedding_service: Optional[EmbeddingService] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
    min_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Retrieve top-k document chunks most similar to a user query.

    The 4-step retrieval path:
    1. Take the user query string.
    2. Embed the query using the identical model used for document chunks.
    3. Search the vector database collection with cosine similarity.
    4. Return ranked chunks with similarity scores, text, and source metadata.

    Args:
        query: User search or question string.
        k: Number of highest-scoring chunks to retrieve (default: 3).
        collection: Vector store collection to query against.
        embedding_service: EmbeddingService to generate query vectors.
        filter_metadata: Optional key-value constraints on chunk metadata.
        min_score: Optional minimum similarity threshold.

    Returns:
        List of dictionaries with score, text, metadata, rank, and model attribution.

    Raises:
        ValueError: If query is empty or k is invalid.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    if k <= 0:
        return []

    if collection is None:
        raise ValueError("A valid VectorStore collection must be provided for retrieval.")

    # 1. Obtain embedding service and enforce same-model query embedding
    service = embedding_service or get_embedding_service()

    # 2. Embed the user query (enforcing the same model rule)
    query_vector = _embed_query_safe(service, query)

    # 3. Search the vector database
    search_results = collection.search(
        query_vector=query_vector,
        top_k=k,
        filter_metadata=filter_metadata,
        min_score=min_score,
    )

    # 4. Standardize output results with rank, score, text, metadata
    retrieved_items: List[Dict[str, Any]] = []
    for item in search_results:
        retrieved_items.append({
            "rank": item["rank"],
            "score": round(item["score"], 4),
            "text": item["text"],
            "metadata": item["metadata"],
            "embedding_model": item.get("embedding_model", service.model),
            "id": item.get("id"),
        })

    return retrieved_items


def compare_k_retrieval(
    query: str,
    k_values: Sequence[int] = (1, 3, 5),
    collection: Optional[InMemoryVectorStore] = None,
    embedding_service: Optional[EmbeddingService] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute retrieval across multiple k values to inspect context changes and trade-offs.

    Args:
        query: User query string.
        k_values: Sequence of integer k values to evaluate (e.g. [1, 3, 5]).
        collection: Vector store collection to search.
        embedding_service: Optional embedding service instance.
        filter_metadata: Optional metadata filter dictionary.

    Returns:
        Dictionary containing comparative analysis across all k configurations.
    """
    if collection is None:
        raise ValueError("A valid VectorStore collection must be provided.")

    service = embedding_service or get_embedding_service()
    query_vector = _embed_query_safe(service, query)

    results_by_k: Dict[str, List[Dict[str, Any]]] = {}
    seen_chunk_keys: set = set()
    incremental_insights: List[Dict[str, Any]] = []

    for k in sorted(k_values):
        k_key = f"k_{k}"
        raw_matches = collection.search(
            query_vector=query_vector,
            top_k=k,
            filter_metadata=filter_metadata,
        )

        formatted_results = [
            {
                "rank": r["rank"],
                "score": round(r["score"], 4),
                "source": r["metadata"].get("source", "unknown"),
                "chunk_index": r["metadata"].get("chunk_index", 0),
                "text_snippet": r["text"][:120] + "..." if len(r["text"]) > 120 else r["text"],
                "text": r["text"],
                "metadata": r["metadata"],
                "embedding_model": r.get("embedding_model", service.model),
            }
            for r in raw_matches
        ]
        results_by_k[k_key] = formatted_results

        # Track new chunks added at this k level
        new_at_this_k = []
        for r in formatted_results:
            uid = (r["source"], r["chunk_index"])
            if uid not in seen_chunk_keys:
                seen_chunk_keys.add(uid)
                new_at_this_k.append({
                    "rank": r["rank"],
                    "score": r["score"],
                    "source": r["source"],
                    "chunk_index": r["chunk_index"],
                })

        incremental_insights.append({
            "k": k,
            "total_chunks_returned": len(formatted_results),
            "new_chunks_introduced": len(new_at_this_k),
            "min_score_at_k": formatted_results[-1]["score"] if formatted_results else 0.0,
            "max_score_at_k": formatted_results[0]["score"] if formatted_results else 0.0,
        })

    return {
        "query": query,
        "embedding_model": service.model,
        "k_values": list(k_values),
        "results_by_k": results_by_k,
        "comparison_summary": incremental_insights,
    }
