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
    collection: Optional[Union[InMemoryVectorStore, Any]] = None,
    embedding_service: Optional[EmbeddingService] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
    min_score: Optional[float] = None,
    *,
    metadata_filter: Optional[Dict[str, Any]] = None,
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
        metadata_filter: Alias for filter_metadata.

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

    effective_filter = filter_metadata or metadata_filter

    # 1. Obtain embedding service and enforce same-model query embedding
    service = embedding_service or get_embedding_service()

    # 2. Embed the user query (enforcing the same model rule)
    query_vector = _embed_query_safe(service, query)

    # 3. Search the vector database
    search_results = collection.search(
        query_vector=query_vector,
        top_k=k,
        filter_metadata=effective_filter,
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


def keyword_score(text: str, keywords: Sequence[str]) -> int:
    """Compute lexical keyword occurrence count in text.

    Args:
        text: Document chunk string.
        keywords: List of target words/phrases to match.

    Returns:
        Integer count of matched keywords in the text (case-insensitive).
    """
    if not text or not keywords:
        return 0
    lowered = text.lower()
    return sum(1 for word in keywords if word.lower() in lowered)


def hybrid_rank(
    vector_results: Sequence[Dict[str, Any]],
    keywords: Sequence[str],
    vector_weight: float = 0.8,
    keyword_weight: float = 0.2,
) -> List[Dict[str, Any]]:
    """Combine vector semantic similarity and lexical keyword scoring.

    Formula:
        hybrid_score = (vector_weight * vector_score) + (keyword_weight * keyword_score)

    Args:
        vector_results: List of retrieval result dictionaries (containing 'score' and 'text').
        keywords: Sequence of target keyword terms to reward.
        vector_weight: Weight assigned to semantic vector similarity (default: 0.8).
        keyword_weight: Weight assigned to lexical keyword score (default: 0.2).

    Returns:
        Sorted list of ranked results descending by hybrid_score, with rank,
        keyword_score, and hybrid_score annotated.
    """
    ranked: List[Dict[str, Any]] = []
    for item in vector_results:
        lexical = keyword_score(item.get("text", ""), keywords)
        vec_score = float(item.get("score", 0.0))
        combined = (vector_weight * vec_score) + (keyword_weight * lexical)
        result_entry = dict(item)
        result_entry["keyword_score"] = lexical
        result_entry["hybrid_score"] = round(combined, 4)
        ranked.append(result_entry)

    # Sort descending by hybrid_score, breaking ties with vector similarity
    ranked.sort(key=lambda item: (item["hybrid_score"], item.get("score", 0.0)), reverse=True)

    for rank_idx, item in enumerate(ranked, start=1):
        item["rank"] = rank_idx

    return ranked


def hybrid_retrieve(
    query: str,
    keywords: Optional[Sequence[str]] = None,
    k: int = 3,
    collection: Optional[Union[InMemoryVectorStore, Any]] = None,
    embedding_service: Optional[EmbeddingService] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
    vector_weight: float = 0.8,
    keyword_weight: float = 0.2,
    min_score: Optional[float] = None,
    *,
    metadata_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Execute end-to-end vector retrieval with metadata filtering and keyword hybrid ranking.

    Args:
        query: User search query.
        keywords: Optional list of exact keyword tokens to match (defaults to query words).
        k: Top-k candidates to retrieve.
        collection: Vector store collection.
        embedding_service: Optional EmbeddingService.
        filter_metadata: Optional metadata filter dict.
        vector_weight: Weight for dense similarity.
        keyword_weight: Weight for keyword frequency.
        min_score: Minimum vector similarity threshold.
        metadata_filter: Alias for filter_metadata.

    Returns:
        List of reranked hybrid search result items.
    """
    effective_filter = filter_metadata or metadata_filter
    base_results = retrieve(
        query=query,
        k=k,
        collection=collection,
        embedding_service=embedding_service,
        filter_metadata=effective_filter,
        min_score=min_score,
    )

    effective_keywords = (
        keywords
        if keywords is not None
        else [w.strip() for w in query.split() if len(w.strip()) > 2]
    )
    if not effective_keywords:
        return base_results

    return hybrid_rank(
        vector_results=base_results,
        keywords=effective_keywords,
        vector_weight=vector_weight,
        keyword_weight=keyword_weight,
    )


def show_results(label: str, results: Sequence[Dict[str, Any]], max_chars: int = 120) -> None:
    """Print formatted search results for easy comparison in terminal demonstrations.

    Args:
        label: Header label (e.g. 'unfiltered', 'filtered', 'hybrid filtered').
        results: Sequence of result dictionaries.
        max_chars: Maximum characters of text snippet to show.
    """
    print(f"\n=== {label.upper()} (Count: {len(results)}) ===")
    for item in results:
        score_val = item.get("score")
        score_str = f"{score_val:.4f}" if isinstance(score_val, (int, float)) else "N/A"
        print("score:", score_str)
        if "hybrid_score" in item:
            print("hybrid_score:", f"{item['hybrid_score']:.4f}")
        if "keyword_score" in item:
            print("keyword_score:", item["keyword_score"])
        meta = item.get("metadata", {})
        print("source:", meta.get("source", "unknown"))
        print("section:", meta.get("section"))
        txt = item.get("text", "")
        print("text:", txt[:max_chars].strip())
        print("-" * 40)


def compare_filtered_unfiltered(
    query: str,
    filter_metadata: Dict[str, Any],
    keywords: Optional[Sequence[str]] = None,
    k: int = 3,
    collection: Optional[Union[InMemoryVectorStore, Any]] = None,
    embedding_service: Optional[EmbeddingService] = None,
    vector_weight: float = 0.8,
    keyword_weight: float = 0.2,
) -> Dict[str, Any]:
    """Execute and compare unfiltered, filtered, and hybrid-filtered retrieval for a query.

    Args:
        query: User search query.
        filter_metadata: Filter dictionary to constrain document metadata.
        keywords: Optional keywords for hybrid scoring.
        k: Top-k items to retrieve.
        collection: Vector store instance.
        embedding_service: EmbeddingService instance.
        vector_weight: Hybrid vector weight.
        keyword_weight: Hybrid keyword weight.

    Returns:
        Structured dictionary comparing unfiltered, filtered, and hybrid results with precision metrics.
    """
    unfiltered = retrieve(
        query=query,
        k=k,
        collection=collection,
        embedding_service=embedding_service,
        filter_metadata=None,
    )

    filtered = retrieve(
        query=query,
        k=k,
        collection=collection,
        embedding_service=embedding_service,
        filter_metadata=filter_metadata,
    )

    effective_kw = keywords or [w.strip() for w in query.split() if len(w.strip()) > 2]
    hybrid_filtered = hybrid_rank(
        vector_results=filtered,
        keywords=effective_kw,
        vector_weight=vector_weight,
        keyword_weight=keyword_weight,
    )

    filtered_ids = {item.get("id") or item.get("text") for item in filtered}

    removed_distractors = [
        item for item in unfiltered
        if (item.get("id") or item.get("text")) not in filtered_ids
    ]

    return {
        "query": query,
        "filter": filter_metadata,
        "keywords": list(effective_kw),
        "k": k,
        "unfiltered_results": unfiltered,
        "filtered_results": filtered,
        "hybrid_results": hybrid_filtered,
        "metrics": {
            "unfiltered_count": len(unfiltered),
            "filtered_count": len(filtered),
            "removed_irrelevant_chunks_count": len(removed_distractors),
            "top_unfiltered_section": unfiltered[0]["metadata"].get("section") if unfiltered else None,
            "top_filtered_section": filtered[0]["metadata"].get("section") if filtered else None,
            "top_hybrid_score": hybrid_filtered[0]["hybrid_score"] if hybrid_filtered else None,
        },
    }


def compare_k_retrieval(
    query: str,
    k_values: Sequence[int] = (1, 3, 5),
    collection: Optional[Union[InMemoryVectorStore, Any]] = None,
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
