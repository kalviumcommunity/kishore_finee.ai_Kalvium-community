"""Retrieval engine module for FInee.ai.

Responsible for semantic similarity calculation, chunk ranking,
and embedding retrieval sanity testing.
"""

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

__all__ = [
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
