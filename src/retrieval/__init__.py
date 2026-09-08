"""Retrieval engine module for finee.ai.

Responsible for semantic similarity search, compliance metadata filtering,
Top-K document chunk retrieval, sanity checking, vector stores, and candidate re-ranking.
"""

from src.retrieval.chroma_store import ChromaVectorStore
from src.retrieval.reranker import (
    RerankConfigurationError,
    RerankError,
    RerankScoringError,
    format_rerank_comparison,
    parse_rerank_score,
    rerank,
    retrieve_and_rerank,
    score_relevance,
)
from src.retrieval.retriever import (
    RetrievalResult,
    compare_filtered_unfiltered,
    compare_k_retrieval,
    hybrid_rank,
    hybrid_retrieve,
    keyword_score,
    retrieve,
    show_results,
)
from src.retrieval.sanity_checker import (
    DimensionMismatchError,
    InvalidVectorError,
    ModelMismatchError,
    RetrievalError,
    SAMPLE_CHUNK_RECORDS,
    SAMPLE_SANITY_TEST_CASES,
    cosine_similarity,
    generate_sanity_report,
    rank_chunks,
    run_sanity_tests,
)
from src.retrieval.vector_store import (
    InMemoryVectorStore,
    VectorRecord,
)

__all__ = [
    "InMemoryVectorStore",
    "ChromaVectorStore",
    "VectorRecord",
    "RetrievalResult",
    "retrieve",
    "keyword_score",
    "hybrid_rank",
    "hybrid_retrieve",
    "show_results",
    "compare_filtered_unfiltered",
    "compare_k_retrieval",
    "rerank",
    "retrieve_and_rerank",
    "format_rerank_comparison",
    "score_relevance",
    "parse_rerank_score",
    "RerankError",
    "RerankConfigurationError",
    "RerankScoringError",
    "DimensionMismatchError",
    "InvalidVectorError",
    "ModelMismatchError",
    "RetrievalError",
    "SAMPLE_CHUNK_RECORDS",
    "SAMPLE_SANITY_TEST_CASES",
    "cosine_similarity",
    "generate_sanity_report",
    "rank_chunks",
    "run_sanity_tests",
]
