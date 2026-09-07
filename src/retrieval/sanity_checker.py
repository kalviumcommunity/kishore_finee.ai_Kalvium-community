"""Embedding retrieval sanity testing module for finee.ai.

Provides deterministic similarity calculation, chunk ranking, model validation,
and test running with failure diagnostics for embedding verification.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np

from src.core.config import settings

logger = logging.getLogger(__name__)


class RetrievalError(Exception):
    """Base exception for retrieval and ranking errors."""
    pass


class ModelMismatchError(RetrievalError):
    """Raised when query and chunk embeddings were generated with different models."""
    pass


class DimensionMismatchError(RetrievalError):
    """Raised when query and chunk vector dimensions do not match."""
    pass


class InvalidVectorError(RetrievalError):
    """Raised when embedding vectors are empty, non-numeric, or have zero norm."""
    pass


def cosine_similarity(
    vec_a: Sequence[float] | np.ndarray,
    vec_b: Sequence[float] | np.ndarray,
    allow_zero_norm: bool = False,
) -> float:
    """Calculate the cosine similarity between two numeric vectors.

    Formula:
        cosine_similarity(A, B) = (A · B) / (||A|| * ||B||)

    Args:
        vec_a: First vector of float numbers.
        vec_b: Second vector of float numbers.
        allow_zero_norm: If True, returns 0.0 on zero-norm vectors instead of raising an error.

    Returns:
        Float value between -1.0 and 1.0.

    Raises:
        InvalidVectorError: If vectors are empty, non-numeric, contain NaN/Inf, or have zero norm.
        DimensionMismatchError: If vectors have mismatched lengths.
    """
    if len(vec_a) == 0 or len(vec_b) == 0:
        raise InvalidVectorError("Cannot compute cosine similarity of empty vectors.")

    if len(vec_a) != len(vec_b):
        raise DimensionMismatchError(
            f"Vector dimensions must match for cosine similarity: {len(vec_a)} vs {len(vec_b)}"
        )

    try:
        a = np.asarray(vec_a, dtype=np.float64)
        b = np.asarray(vec_b, dtype=np.float64)
    except (ValueError, TypeError) as err:
        raise InvalidVectorError(f"Vector contains non-numeric values: {err}") from err

    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise InvalidVectorError("Vector contains NaN or infinite values.")

    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))

    if norm_a == 0.0 or norm_b == 0.0:
        if allow_zero_norm:
            return 0.0
        raise InvalidVectorError("Cannot compute cosine similarity with a zero-norm vector.")

    sim = float(np.dot(a, b) / (norm_a * norm_b))
    return max(-1.0, min(1.0, sim))


def rank_chunks(
    query: Union[str, Sequence[float]],
    chunk_records: Sequence[Dict[str, Any]],
    embedding_service: Optional[Any] = None,
    validate_model: bool = True,
    expected_model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Rank chunk records by cosine similarity to a search query.

    Args:
        query: Query text string or pre-computed embedding vector.
        chunk_records: List of chunk dictionaries containing text, metadata, and embedding.
        embedding_service: Optional EmbeddingService instance to embed query strings.
        validate_model: If True, enforces that chunk embedding_model matches query model.
        expected_model: Optional model name to validate chunk embeddings against.

    Returns:
        New list of chunk records with added 'score' field, sorted descending by similarity.

    Raises:
        ValueError: If query or chunk records are invalid.
        ModelMismatchError: If a chunk was embedded with a different model.
        DimensionMismatchError: If vector dimensions do not match.
        InvalidVectorError: If vector values are invalid.
    """
    if not chunk_records:
        return []

    # 1. Resolve query vector and model
    if isinstance(query, str):
        if not query.strip():
            raise ValueError("Query text cannot be empty.")

        if embedding_service is None:
            from src.embeddings.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()

        query_vec = embedding_service.embed_query(query)
        query_model = getattr(embedding_service, "model", settings.EMBEDDING_MODEL)
    elif isinstance(query, (list, tuple, np.ndarray)):
        query_vec = list(query)
        query_model = expected_model or settings.EMBEDDING_MODEL
    else:
        raise ValueError(f"Query must be a string or vector sequence, got {type(query).__name__}")

    if len(query_vec) == 0:
        raise InvalidVectorError("Query embedding vector cannot be empty.")

    # 2. Score each chunk
    ranked: List[Dict[str, Any]] = []

    for idx, record in enumerate(chunk_records):
        if not isinstance(record, dict):
            raise ValueError(f"Chunk record at index {idx} must be a dictionary.")

        chunk_vec = record.get("embedding")
        if chunk_vec is None:
            raise InvalidVectorError(
                f"Chunk at index {idx} (source: {record.get('metadata', {}).get('source', 'unknown')}) "
                f"is missing 'embedding' vector."
            )

        # Enforce model consistency
        if validate_model and query_model:
            chunk_model = record.get("embedding_model")
            if chunk_model and chunk_model != query_model:
                raise ModelMismatchError(
                    f"Model mismatch at index {idx}: Query uses '{query_model}', but chunk from "
                    f"'{record.get('metadata', {}).get('source', 'unknown')}' was embedded with '{chunk_model}'. "
                    f"Incompatible embedding spaces cannot be compared."
                )

        score = cosine_similarity(query_vec, chunk_vec)

        # Preserve original record without mutating input
        record_copy = {**record, "score": float(score)}
        ranked.append(record_copy)

    # 3. Sort descending by similarity score
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def run_sanity_tests(
    test_cases: Sequence[Dict[str, Any]],
    chunk_records: Sequence[Dict[str, Any]],
    embedding_service: Optional[Any] = None,
    top_k: int = 1,
) -> Dict[str, Any]:
    """Execute deterministic retrieval sanity tests on known query/source pairs.

    Args:
        test_cases: List of test cases, each containing 'query' and 'expected_source'.
        chunk_records: Corpus chunk records with embeddings and metadata.
        embedding_service: Optional embedding service for query embedding.
        top_k: Number of top results to check for expected source (default: 1).

    Returns:
        Dictionary containing overall statistics and per-test diagnostic details.
    """
    if not test_cases:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "results": [],
        }

    corpus_sources = {
        rec.get("metadata", {}).get("source")
        for rec in chunk_records
        if isinstance(rec, dict) and "metadata" in rec
    }

    results: List[Dict[str, Any]] = []

    for case in test_cases:
        query = case.get("query", "")
        expected_source = case.get("expected_source", "")
        expected_chunk_id = case.get("expected_chunk_id")
        case_top_k = case.get("expected_top_k", top_k)

        try:
            ranked = rank_chunks(
                query=query,
                chunk_records=chunk_records,
                embedding_service=embedding_service,
            )

            if not ranked:
                results.append({
                    "query": query,
                    "expected_source": expected_source,
                    "top_source": None,
                    "top_score": 0.0,
                    "passed": False,
                    "diagnostics": "No chunk records available to rank.",
                    "top_candidates": [],
                })
                continue

            top_candidates = ranked[:case_top_k]
            top_result = ranked[0]
            top_source = top_result.get("metadata", {}).get("source")
            top_score = top_result.get("score", 0.0)

            # Check if expected source is within top_k
            source_match = any(
                c.get("metadata", {}).get("source") == expected_source
                for c in top_candidates
            )

            # Optional chunk index check
            chunk_match = True
            if expected_chunk_id is not None:
                chunk_match = any(
                    c.get("metadata", {}).get("chunk_index") == expected_chunk_id
                    for c in top_candidates
                )

            passed = bool(source_match and chunk_match)
            diagnostics: Optional[str] = None

            if not passed:
                if expected_source not in corpus_sources:
                    diagnostics = (
                        f"Expected source '{expected_source}' is not present in the chunk corpus. "
                        f"Available sources: {sorted(list(corpus_sources))}."
                    )
                elif top_score < 0.2:
                    diagnostics = (
                        f"Low overall similarity score ({top_score:.4f}). "
                        f"The query may be too generic or out-of-domain."
                    )
                else:
                    diagnostics = (
                        f"Top retrieved source '{top_source}' (score: {top_score:.4f}) outranked "
                        f"expected source '{expected_source}'. Inspect candidates for semantic overlap or cleaning issues."
                    )

            candidate_summaries = [
                {
                    "source": c.get("metadata", {}).get("source"),
                    "chunk_index": c.get("metadata", {}).get("chunk_index"),
                    "score": round(c.get("score", 0.0), 4),
                    "text": c.get("text", "")[:100],
                }
                for c in ranked[:3]
            ]

            results.append({
                "query": query,
                "expected_source": expected_source,
                "top_source": top_source,
                "top_score": round(top_score, 4),
                "passed": passed,
                "diagnostics": diagnostics,
                "top_candidates": candidate_summaries,
            })

        except Exception as exc:
            results.append({
                "query": query,
                "expected_source": expected_source,
                "top_source": None,
                "top_score": 0.0,
                "passed": False,
                "diagnostics": f"Pipeline execution error: {type(exc).__name__}: {exc}",
                "top_candidates": [],
            })

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["passed"])
    failed_tests = total_tests - passed_tests
    pass_rate = round((passed_tests / total_tests) * 100.0, 1) if total_tests > 0 else 0.0

    return {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "pass_rate": pass_rate,
        "results": results,
    }


def generate_sanity_report(results: Dict[str, Any]) -> str:
    """Generate a clean, human-readable sanity testing report string.

    Args:
        results: Results dictionary returned by run_sanity_tests.

    Returns:
        Formatted multi-line report string.
    """
    total = results.get("total", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    pass_rate = results.get("pass_rate", 0.0)

    lines: List[str] = [
        "Embedding Sanity Report",
        "=" * 23,
        "",
        f"Tests: {total}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        "",
    ]

    for item in results.get("results", []):
        status = "[PASS]" if item.get("passed") else "[FAIL]"
        query = item.get("query", "")
        expected = item.get("expected_source", "")
        top_source = item.get("top_source", "None")
        top_score = item.get("top_score", 0.0)

        lines.append(status)
        lines.append(f"Query: {query}")
        lines.append(f"Expected source: {expected}")
        lines.append(f"Top source: {top_source}")
        lines.append(f"Top score: {top_score:.4f}")

        if not item.get("passed") and item.get("diagnostics"):
            lines.append(f"Diagnostics: {item['diagnostics']}")

        lines.append("")

    lines.extend([
        "Summary:",
        f"- Total tests: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Pass rate: {pass_rate:.1f}%",
    ])

    return "\n".join(lines)


# ==============================================================================
# Deterministic Test Fixtures
# ==============================================================================

SAMPLE_SANITY_TEST_CASES = [
    {
        "query": "What is the advisory fee structure and billing schedule?",
        "expected_source": "fee-schedule.pdf",
    },
    {
        "query": "When does the bond fund mature and what is its annual yield?",
        "expected_source": "fund-factsheet.pdf",
    },
    {
        "query": "How is customer identity verified under KYC and AML rules?",
        "expected_source": "compliance-policy.pdf",
    },
    {
        "query": "What are the account security requirements for password resets?",
        "expected_source": "account-security.pdf",
    },
    {
        "query": "What is the penalty for early withdrawal from fixed term deposits?",
        "expected_source": "deposit-agreement.pdf",
    },
]

# 5-dimensional orthogonal prototype vectors for deterministic offline testing
_VEC_DIM = 5

SAMPLE_CHUNK_RECORDS = [
    {
        "text": "The annual advisory fee is 0.75% of assets under management, billed quarterly in arrears.",
        "metadata": {
            "source": "fee-schedule.pdf",
            "document_id": "doc_fee_01",
            "document_version": "1.0",
            "chunk_index": 0,
            "page": 1,
            "section": "Advisory Fee Schedule",
            "approval_status": "approved",
        },
        "embedding": [0.95, 0.05, 0.02, 0.01, 0.01],
        "embedding_model": "text-embedding-3-small",
    },
    {
        "text": "The Balanced Bond Fund matures on 31 December 2030 with an annual distribution yield of 4.2%.",
        "metadata": {
            "source": "fund-factsheet.pdf",
            "document_id": "doc_fund_01",
            "document_version": "2.1",
            "chunk_index": 0,
            "page": 2,
            "section": "Fund Maturity & Yield",
            "approval_status": "approved",
        },
        "embedding": [0.03, 0.96, 0.04, 0.02, 0.01],
        "embedding_model": "text-embedding-3-small",
    },
    {
        "text": "Customer Due Diligence (CDD) and AML verification require government ID and proof of address.",
        "metadata": {
            "source": "compliance-policy.pdf",
            "document_id": "doc_comp_01",
            "document_version": "3.0",
            "chunk_index": 0,
            "page": 5,
            "section": "KYC Identity Verification",
            "approval_status": "approved",
        },
        "embedding": [0.02, 0.03, 0.95, 0.04, 0.02],
        "embedding_model": "text-embedding-3-small",
    },
    {
        "text": "Password resets require multi-factor authentication (MFA) and a 12-character passphrase.",
        "metadata": {
            "source": "account-security.pdf",
            "document_id": "doc_sec_01",
            "document_version": "1.2",
            "chunk_index": 0,
            "page": 1,
            "section": "Password Reset Procedures",
            "approval_status": "approved",
        },
        "embedding": [0.01, 0.02, 0.03, 0.97, 0.03],
        "embedding_model": "text-embedding-3-small",
    },
    {
        "text": "Early withdrawal before the 12-month fixed deposit tenure incurs a forfeit of 3 months accrued interest.",
        "metadata": {
            "source": "deposit-agreement.pdf",
            "document_id": "doc_dep_01",
            "document_version": "1.0",
            "chunk_index": 0,
            "page": 3,
            "section": "Early Withdrawal Penalties",
            "approval_status": "approved",
        },
        "embedding": [0.02, 0.01, 0.02, 0.02, 0.96],
        "embedding_model": "text-embedding-3-small",
    },
]


def main() -> None:
    """Run embedding retrieval sanity tests CLI entry point."""
    print("=" * 60)
    print("FInee.ai - EMBEDDING RETRIEVAL SANITY TESTS")
    print("=" * 60)
    print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"Similarity Metric: Cosine Similarity")
    print("-" * 60)

    # Use deterministic vectors for queries matching the prototype chunk dimensions
    query_vectors = {
        "What is the advisory fee structure and billing schedule?": [0.93, 0.04, 0.03, 0.02, 0.01],
        "When does the bond fund mature and what is its annual yield?": [0.02, 0.94, 0.03, 0.02, 0.01],
        "How is customer identity verified under KYC and AML rules?": [0.01, 0.02, 0.96, 0.03, 0.02],
        "What are the account security requirements for password resets?": [0.02, 0.01, 0.02, 0.95, 0.02],
        "What is the penalty for early withdrawal from fixed term deposits?": [0.01, 0.02, 0.01, 0.03, 0.95],
    }

    # Evaluate test cases
    test_results: List[Dict[str, Any]] = []
    for case in SAMPLE_SANITY_TEST_CASES:
        query_text = case["query"]
        expected_src = case["expected_source"]
        q_vec = query_vectors.get(query_text, [0.9, 0.0, 0.0, 0.0, 0.0])

        ranked = rank_chunks(
            query=q_vec,
            chunk_records=SAMPLE_CHUNK_RECORDS,
            validate_model=True,
            expected_model="text-embedding-3-small",
        )

        top_chunk = ranked[0]
        top_src = top_chunk["metadata"]["source"]
        top_sc = top_chunk["score"]
        passed = (top_src == expected_src)

        test_results.append({
            "query": query_text,
            "expected_source": expected_src,
            "top_source": top_src,
            "top_score": round(top_sc, 4),
            "passed": passed,
            "diagnostics": None if passed else f"Mismatched source: {top_src} != {expected_src}",
            "top_candidates": [
                {
                    "source": c["metadata"]["source"],
                    "chunk_index": c["metadata"]["chunk_index"],
                    "score": round(c["score"], 4),
                    "text": c["text"][:80],
                }
                for c in ranked[:3]
            ],
        })

    summary = {
        "total": len(test_results),
        "passed": sum(1 for r in test_results if r["passed"]),
        "failed": len(test_results) - sum(1 for r in test_results if r["passed"]),
        "pass_rate": round(sum(1 for r in test_results if r["passed"]) / len(test_results) * 100, 1),
        "results": test_results,
    }

    report = generate_sanity_report(summary)
    print("\n" + report)


if __name__ == "__main__":
    main()
