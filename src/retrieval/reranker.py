"""Re-ranking service module for finee.ai RAG platform.

Takes a larger candidate set retrieved via initial vector search, scores each
query/chunk pair using a focused relevance evaluator, and returns the top-k results
while preserving original provenance metadata and initial vector similarity scores.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)

RERANK_PROMPT_TEMPLATE = """Score how relevant the following chunk is to the query from 0 to 10.

Query:
{query}

Chunk:
{chunk_text}

Return only the numeric score."""


class RerankError(Exception):
    """Base exception for re-ranking operations."""
    pass


class RerankConfigurationError(RerankError, ValueError):
    """Raised when re-ranking configuration (candidate_k, final_k) is invalid."""
    pass


class RerankScoringError(RerankError):
    """Raised when re-ranking scoring fails or output is malformed."""
    pass


def parse_rerank_score(response_text: str, fallback_score: float = 5.0) -> float:
    """Parse and normalize a numeric relevance score (0–10) from model output.

    Args:
        response_text: Raw string returned by the scoring model.
        fallback_score: Default score to return if no number can be extracted.

    Returns:
        Float value clamped between 0.0 and 10.0.
    """
    if not response_text or not isinstance(response_text, str):
        return fallback_score

    # Find first integer or floating point number in text
    match = re.search(r"[-+]?(?:\d*\.\d+|\d+)", response_text.strip())
    if not match:
        logger.warning("No numeric score found in model output '%s', using fallback %s", response_text, fallback_score)
        return fallback_score

    try:
        val = float(match.group(0))
        # Clamp score to allowed 0 to 10 scale
        return max(0.0, min(10.0, val))
    except (ValueError, TypeError):
        return fallback_score


def _deterministic_relevance_scorer(query: str, chunk_text: str) -> float:
    """Deterministic scoring heuristic for offline testing and fallback execution.

    Evaluates exact keyword matches, n-gram lexical overlap, and key financial term
    density without calling external paid APIs.

    Args:
        query: User search query.
        chunk_text: Document chunk string.

    Returns:
        Calibrated float score between 0.0 and 10.0.
    """
    if not query or not chunk_text:
        return 0.0

    q_clean = query.lower()
    c_clean = chunk_text.lower()

    q_words = re.findall(r"\b\w+\b", q_clean)
    if not q_words:
        return 0.0

    # 1. Exact unigram overlap ratio
    matched_unigrams = sum(1 for w in q_words if w in c_clean)
    unigram_ratio = matched_unigrams / len(q_words)

    # 2. Bigram phrase overlap
    bigram_matches = 0
    total_bigrams = max(1, len(q_words) - 1)
    for i in range(len(q_words) - 1):
        bigram = f"{q_words[i]} {q_words[i+1]}"
        if bigram in c_clean:
            bigram_matches += 1
    bigram_ratio = bigram_matches / total_bigrams

    # 3. Financial domain term density bonus
    financial_keywords = [
        "fee", "advisory", "schedule", "yield", "bond", "fund",
        "compliance", "kyc", "aml", "security", "penalty", "deposit",
        "billing", "quarterly", "interest", "annual", "rate", "matur"
    ]
    domain_hits = sum(1 for kw in financial_keywords if kw in q_clean and kw in c_clean)
    domain_bonus = min(2.0, domain_hits * 0.5)

    # Combine into 0–10 scale
    base_score = (unigram_ratio * 5.0) + (bigram_ratio * 3.0) + domain_bonus
    return max(0.0, min(10.0, round(base_score, 2)))


def score_relevance(
    query: str,
    chunk_text: str,
    model: Optional[str] = None,
    timeout: float = 5.0,
) -> float:
    """Score the relevance of a chunk to a query on a 0–10 scale.

    If an API key is available (OpenAI or Groq), evaluates using the configured LLM API.
    Otherwise, falls back safely to calibrated deterministic scoring.

    Args:
        query: Search query string.
        chunk_text: Text of the candidate chunk.
        model: Optional model override.
        timeout: Request timeout in seconds.

    Returns:
        Float relevance score between 0.0 and 10.0.
    """
    api_key = settings.OPENAI_API_KEY or settings.GROQ_API_KEY
    base_url = settings.OPENAI_BASE_URL or settings.GROQ_BASE_URL or "https://api.openai.com/v1"
    target_model = model or settings.RERANK_MODEL or settings.CHAT_MODEL or "gpt-4o-mini"

    # If no API key configured, use deterministic scoring
    if not api_key or not str(api_key).strip():
        return _deterministic_relevance_scorer(query, chunk_text)

    prompt = RERANK_PROMPT_TEMPLATE.format(query=query.strip(), chunk_text=chunk_text.strip())

    payload = {
        "model": target_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 10,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = f"{base_url.rstrip('/')}/chat/completions"

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return parse_rerank_score(content)
            else:
                logger.warning("LLM re-rank scoring returned status %d: %s. Using fallback.", resp.status_code, resp.text)
                return _deterministic_relevance_scorer(query, chunk_text)
    except Exception as exc:
        logger.warning("LLM re-rank scoring failed: %s. Using fallback.", exc)
        return _deterministic_relevance_scorer(query, chunk_text)


def rerank(
    query: str,
    candidates: Sequence[Dict[str, Any]],
    final_k: Optional[int] = None,
    model: Optional[str] = None,
    scorer: Optional[Callable[[str, str], float]] = None,
) -> List[Dict[str, Any]]:
    """Re-rank candidate chunks by scoring query/chunk relevance and returning top final_k items.

    Args:
        query: User search query string.
        candidates: List of initial retrieved candidate chunks with text, metadata, and score.
        final_k: Number of final top chunks to return (default: settings.RERANK_FINAL_K).
        model: Optional model identifier for scoring.
        scorer: Optional scoring callable accepting (query, chunk_text) -> float.

    Returns:
        New sorted list of top-k candidate chunks with rerank_score attached.

    Raises:
        ValueError: If query is empty or final_k is invalid.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    if not candidates:
        return []

    effective_k = final_k if final_k is not None else settings.RERANK_FINAL_K
    if effective_k <= 0:
        raise ValueError(f"final_k must be a positive integer, got {effective_k}")

    scoring_fn = scorer or (lambda q, c: score_relevance(q, c, model=model))

    reranked: List[Dict[str, Any]] = []

    for idx, cand in enumerate(candidates):
        if not isinstance(cand, dict):
            raise ValueError(f"Candidate at index {idx} must be a dictionary.")

        chunk_text = cand.get("text", "")
        initial_score = cand.get("score", 0.0)

        # Compute re-ranking relevance score
        rel_score = scoring_fn(query, chunk_text)

        # Build new dictionary preserving original candidate attributes
        entry = {
            **cand,
            "score": round(float(initial_score), 4),
            "rerank_score": round(float(rel_score), 4),
        }
        reranked.append(entry)

    # Sort descending by rerank_score, using initial vector score as tie-breaker
    reranked.sort(
        key=lambda item: (item["rerank_score"], item.get("score", 0.0)),
        reverse=True,
    )

    # Slice top final_k results and update rank
    top_results = reranked[:effective_k]
    for new_rank, item in enumerate(top_results, start=1):
        item["rank"] = new_rank

    return top_results


def retrieve_and_rerank(
    query: str,
    candidate_k: Optional[int] = None,
    final_k: Optional[int] = None,
    collection: Optional[Any] = None,
    filter_metadata: Optional[Dict[str, Any]] = None,
    embedding_service: Optional[Any] = None,
    model: Optional[str] = None,
    scorer: Optional[Callable[[str, str], float]] = None,
) -> Dict[str, Any]:
    """Execute end-to-end vector retrieval followed by candidate re-ranking with latency tracking.

    Args:
        query: User search query.
        candidate_k: Number of initial candidates to retrieve (default: settings.RERANK_CANDIDATE_K).
        final_k: Number of top re-ranked candidates to return (default: settings.RERANK_FINAL_K).
        collection: VectorStore collection to query against.
        filter_metadata: Optional metadata filter.
        embedding_service: Optional EmbeddingService instance.
        model: Optional re-ranking model override.
        scorer: Optional custom scoring callable.

    Returns:
        Dictionary containing initial candidates, re-ranked results, and timing metrics.

    Raises:
        RerankConfigurationError: If candidate_k or final_k values are invalid.
    """
    cand_k = candidate_k if candidate_k is not None else settings.RERANK_CANDIDATE_K
    fin_k = final_k if final_k is not None else settings.RERANK_FINAL_K

    if cand_k <= 0:
        raise RerankConfigurationError(f"candidate_k must be a positive integer, got {cand_k}")
    if fin_k <= 0:
        raise RerankConfigurationError(f"final_k must be a positive integer, got {fin_k}")
    if fin_k > cand_k:
        raise RerankConfigurationError(
            f"final_k ({fin_k}) cannot be greater than candidate_k ({cand_k}). "
            f"Initial candidate set must be larger than or equal to final results."
        )

    from src.retrieval.retriever import retrieve

    # 1. Measure initial vector retrieval latency
    t0 = time.perf_counter()
    initial_candidates = retrieve(
        query=query,
        k=cand_k,
        collection=collection,
        filter_metadata=filter_metadata,
        embedding_service=embedding_service,
    )
    t1 = time.perf_counter()
    retrieval_latency = t1 - t0

    # 2. Measure re-ranking latency
    reranked_results = rerank(
        query=query,
        candidates=initial_candidates,
        final_k=fin_k,
        model=model,
        scorer=scorer,
    )
    t2 = time.perf_counter()
    rerank_latency = t2 - t1
    total_latency = t2 - t0

    return {
        "query": query,
        "candidate_k": cand_k,
        "final_k": fin_k,
        "initial_candidates": initial_candidates,
        "reranked_results": reranked_results,
        "metrics": {
            "candidate_count": len(initial_candidates),
            "final_count": len(reranked_results),
            "retrieval_latency_seconds": round(retrieval_latency, 4),
            "rerank_latency_seconds": round(rerank_latency, 4),
            "total_latency_seconds": round(total_latency, 4),
            "rerank_calls": len(initial_candidates),
        },
    }


def format_rerank_comparison(pipeline_result: Dict[str, Any]) -> str:
    """Format Before vs After re-ranking ordering comparison report.

    Args:
        pipeline_result: Result dictionary returned by retrieve_and_rerank.

    Returns:
        Multi-line formatted comparison string.
    """
    query = pipeline_result.get("query", "")
    initial = pipeline_result.get("initial_candidates", [])
    reranked = pipeline_result.get("reranked_results", [])
    metrics = pipeline_result.get("metrics", {})

    lines: List[str] = [
        "Re-ranking Retrieval Comparison",
        "=" * 32,
        f"Query: {query}",
        "",
        "Before re-ranking (Initial Vector Retrieval):",
        "-" * 45,
    ]

    for idx, item in enumerate(initial, start=1):
        v_score = item.get("score", 0.0)
        source = item.get("metadata", {}).get("source", "unknown")
        preview = item.get("text", "").replace("\n", " ")[:60]
        lines.append(f"{idx}. vector_score={v_score:.4f} source={source} preview=\"{preview}...\"")

    lines.extend([
        "",
        "After re-ranking (Relevance-Scored Top-K):",
        "-" * 45,
    ])

    for idx, item in enumerate(reranked, start=1):
        v_score = item.get("score", 0.0)
        r_score = item.get("rerank_score", 0.0)
        source = item.get("metadata", {}).get("source", "unknown")
        preview = item.get("text", "").replace("\n", " ")[:60]
        lines.append(
            f"{idx}. vector_score={v_score:.4f} rerank_score={r_score:.2f} "
            f"source={source} preview=\"{preview}...\""
        )

    lines.extend([
        "",
        "Performance & Latency Breakdown:",
        "-" * 45,
        f"Initial retrieval candidates: {metrics.get('candidate_count', len(initial))}",
        f"Final results: {metrics.get('final_count', len(reranked))}",
        f"Initial retrieval latency: {metrics.get('retrieval_latency_seconds', 0.0):.4f} seconds",
        f"Re-ranking latency: {metrics.get('rerank_latency_seconds', 0.0):.4f} seconds",
        f"Total latency: {metrics.get('total_latency_seconds', 0.0):.4f} seconds",
        f"Re-ranking calls: {metrics.get('rerank_calls', len(initial))}",
    ])

    return "\n".join(lines)


# ==============================================================================
# Sample Fixtures for CLI Demonstration
# ==============================================================================

SAMPLE_CANDIDATE_CHUNKS = [
    {
        "rank": 1,
        "score": 0.91,
        "text": "General Financial Advisory Overview: Marcus and wealth management clients receive regular market commentary.",
        "metadata": {"source": "general-guide.md", "chunk_index": 0, "section": "Overview"},
        "embedding_model": "text-embedding-3-small",
        "id": "general-guide.md:0",
    },
    {
        "rank": 2,
        "score": 0.89,
        "text": "The annual advisory fee is 0.75% of assets under management, billed quarterly in arrears on invoice #FEE-2026.",
        "metadata": {"source": "fee-schedule.pdf", "chunk_index": 0, "section": "Fee Terms"},
        "embedding_model": "text-embedding-3-small",
        "id": "fee-schedule.pdf:0",
    },
    {
        "rank": 3,
        "score": 0.87,
        "text": "The balanced bond fund matures on 31 December 2030 with an annual distribution yield of 4.2%.",
        "metadata": {"source": "fund-factsheet.pdf", "chunk_index": 0, "section": "Bond Yields"},
        "embedding_model": "text-embedding-3-small",
        "id": "fund-factsheet.pdf:0",
    },
    {
        "rank": 4,
        "score": 0.84,
        "text": "Client Advisory Billing Evidence: Advisory fee of $1,250 was billed to Marcus on 20 August and verified.",
        "metadata": {"source": "billing-records.pdf", "chunk_index": 1, "section": "Invoices"},
        "embedding_model": "text-embedding-3-small",
        "id": "billing-records.pdf:1",
    },
    {
        "rank": 5,
        "score": 0.80,
        "text": "KYC Customer Identification: Verified identity through government passport and utility bill.",
        "metadata": {"source": "compliance-policy.pdf", "chunk_index": 0, "section": "Identity"},
        "embedding_model": "text-embedding-3-small",
        "id": "compliance-policy.pdf:0",
    },
]


def main() -> None:
    """CLI demonstration entry point for candidate re-ranking."""
    print("=" * 60)
    print("FInee.ai - RE-RANKING RETRIEVED CANDIDATES")
    print("=" * 60)

    query = "What evidence supports the advisory fee charged to the client?"
    print(f"Query: {query}")
    print(f"Initial Candidates (K={len(SAMPLE_CANDIDATE_CHUNKS)}) -> Final K=3")
    print("-" * 60)

    t0 = time.perf_counter()
    time.sleep(0.015)  # Simulate vector retrieval latency
    t1 = time.perf_counter()

    reranked = rerank(query=query, candidates=SAMPLE_CANDIDATE_CHUNKS, final_k=3)
    t2 = time.perf_counter()

    demo_result = {
        "query": query,
        "candidate_k": len(SAMPLE_CANDIDATE_CHUNKS),
        "final_k": 3,
        "initial_candidates": SAMPLE_CANDIDATE_CHUNKS,
        "reranked_results": reranked,
        "metrics": {
            "candidate_count": len(SAMPLE_CANDIDATE_CHUNKS),
            "final_count": len(reranked),
            "retrieval_latency_seconds": round(t1 - t0, 4),
            "rerank_latency_seconds": round(t2 - t1, 4),
            "total_latency_seconds": round(t2 - t0, 4),
            "rerank_calls": len(SAMPLE_CANDIDATE_CHUNKS),
        },
    }

    report = format_rerank_comparison(demo_result)
    print("\n" + report)


if __name__ == "__main__":
    main()
