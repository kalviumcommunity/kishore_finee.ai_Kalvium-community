"""Retrieval Guardrails and Safe Refusal module for finee.ai RAG platform.

Provides retrieval quality evaluation, relevance threshold enforcement, pre-LLM
safe refusal generation, and evaluation diagnostics for compliance-grounded advisory.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

from src.core.config import settings

logger = logging.getLogger(__name__)


def get_chunk_score(chunk: Union[Dict[str, Any], Any]) -> float:
    """Safely extract the numerical relevance or similarity score from a chunk.

    Adapts to existing repository score fields (`score`, `vector_score`, `similarity_score`, `rerank_score`).

    Args:
        chunk: Chunk dictionary or object.

    Returns:
        Float score (defaults to 0.0 if missing, None, or unparseable).
    """
    if isinstance(chunk, dict):
        raw_val = (
            chunk.get("score")
            if chunk.get("score") is not None
            else chunk.get("vector_score")
            if chunk.get("vector_score") is not None
            else chunk.get("similarity_score")
            if chunk.get("similarity_score") is not None
            else chunk.get("rerank_score")
        )
    else:
        raw_val = (
            getattr(chunk, "score", None)
            if getattr(chunk, "score", None) is not None
            else getattr(chunk, "vector_score", None)
            if getattr(chunk, "vector_score", None) is not None
            else getattr(chunk, "similarity_score", None)
            if getattr(chunk, "similarity_score", None) is not None
            else getattr(chunk, "rerank_score", None)
        )

    if raw_val is None:
        return 0.0

    try:
        val = float(raw_val)
        return val
    except (ValueError, TypeError):
        return 0.0


def retrieval_is_strong(
    chunks: Optional[Sequence[Union[Dict[str, Any], Any]]],
    min_top_score: Optional[float] = None,
    min_supporting_chunks: Optional[int] = None,
) -> bool:
    """Determine whether a set of retrieved chunks meets the configured relevance strength threshold.

    Requirements:
      1. Chunk list must not be empty.
      2. Highest-scoring chunk must meet or exceed min_top_score.
      3. At least min_supporting_chunks must meet or exceed min_top_score.

    Args:
        chunks: Sequence of retrieved candidate chunks.
        min_top_score: Minimum required relevance score (default: settings.MIN_TOP_SCORE).
        min_supporting_chunks: Minimum number of chunks required above threshold (default: settings.MIN_SUPPORTING_CHUNKS).

    Returns:
        True if retrieval meets quality guardrails, False otherwise.
    """
    if not chunks:
        return False

    top_thresh = min_top_score if min_top_score is not None else settings.MIN_TOP_SCORE
    support_thresh = min_supporting_chunks if min_supporting_chunks is not None else settings.MIN_SUPPORTING_CHUNKS

    scores = [get_chunk_score(c) for c in chunks]
    top_score = max(scores, default=0.0)

    if top_score < top_thresh:
        return False

    strong_count = sum(1 for s in scores if s >= top_thresh)
    return strong_count >= support_thresh


def evaluate_retrieval_strength(
    chunks: Optional[Sequence[Union[Dict[str, Any], Any]]],
    min_top_score: Optional[float] = None,
    min_supporting_chunks: Optional[int] = None,
) -> Dict[str, Any]:
    """Evaluate retrieval evidence strength and classify refusal reason if insufficient.

    Statuses:
      - `answered`: Strong retrieval meeting all criteria.
      - `refused_empty_context`: 0 chunks retrieved.
      - `refused_weak_context`: Top chunk score is below min_top_score.
      - `refused_insufficient_support`: Fewer than min_supporting_chunks meet min_top_score.

    Args:
        chunks: Candidate chunks retrieved from vector database.
        min_top_score: Minimum required score threshold.
        min_supporting_chunks: Minimum required count of supporting chunks.

    Returns:
        Structured evaluation dictionary containing diagnostic metrics and refusal reasons.
    """
    top_thresh = min_top_score if min_top_score is not None else settings.MIN_TOP_SCORE
    support_thresh = min_supporting_chunks if min_supporting_chunks is not None else settings.MIN_SUPPORTING_CHUNKS

    if not chunks:
        return {
            "is_strong": False,
            "status": "refused_empty_context",
            "top_score": 0.0,
            "supporting_chunks_count": 0,
            "retrieved_chunks_count": 0,
            "min_top_score": top_thresh,
            "min_supporting_chunks": support_thresh,
            "refusal_reason": "No relevant chunks retrieved from knowledge base.",
        }

    scores = [get_chunk_score(c) for c in chunks]
    top_score = max(scores, default=0.0)
    supporting_count = sum(1 for s in scores if s >= top_thresh)

    if top_score < top_thresh:
        return {
            "is_strong": False,
            "status": "refused_weak_context",
            "top_score": round(top_score, 4),
            "supporting_chunks_count": supporting_count,
            "retrieved_chunks_count": len(chunks),
            "min_top_score": top_thresh,
            "min_supporting_chunks": support_thresh,
            "refusal_reason": f"Top retrieval score ({top_score:.4f}) is below minimum threshold ({top_thresh:.4f}).",
        }

    if supporting_count < support_thresh:
        return {
            "is_strong": False,
            "status": "refused_insufficient_support",
            "top_score": round(top_score, 4),
            "supporting_chunks_count": supporting_count,
            "retrieved_chunks_count": len(chunks),
            "min_top_score": top_thresh,
            "min_supporting_chunks": support_thresh,
            "refusal_reason": (
                f"Found {supporting_count} supporting chunk(s) meeting score threshold, "
                f"but minimum {support_thresh} required."
            ),
        }

    return {
        "is_strong": True,
        "status": "answered",
        "top_score": round(top_score, 4),
        "supporting_chunks_count": supporting_count,
        "retrieved_chunks_count": len(chunks),
        "min_top_score": top_thresh,
        "min_supporting_chunks": support_thresh,
        "refusal_reason": None,
    }


async def guarded_answer(
    question: str,
    collection: Optional[Any] = None,
    chunks: Optional[Sequence[Union[Dict[str, Any], Any]]] = None,
    min_top_score: Optional[float] = None,
    min_supporting_chunks: Optional[int] = None,
    top_k: Optional[int] = None,
    use_reranker: Optional[bool] = None,
    refusal_message: Optional[str] = None,
    system_instruction: Optional[str] = None,
    max_context_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    stop_sequences: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute guarded RAG answer pipeline with pre-LLM retrieval strength validation.

    Pipeline:
      1. Retrieve candidate chunks (or use provided candidate list).
      2. Apply re-ranking if enabled.
      3. Evaluate retrieval strength against configured thresholds.
      4. If weak: return safe refusal immediately without invoking LLM.
      5. If strong: assemble context and generate grounded answer with citations.

    Args:
        question: User search or financial advisory question.
        collection: VectorStore collection to query against (if chunks not pre-supplied).
        chunks: Optional pre-retrieved candidate chunks (for testing or direct pipelines).
        min_top_score: Minimum required score threshold.
        min_supporting_chunks: Minimum supporting chunks threshold.
        top_k: Number of candidate chunks to retrieve.
        use_reranker: Toggle to enable/bypass candidate re-ranking.
        refusal_message: Custom refusal message override.
        system_instruction: System prompt override.
        max_context_tokens: Token ceiling for context assembly.
        temperature: LLM temperature override.
        max_tokens: LLM max tokens override.
        top_p: LLM top-p override.
        stop_sequences: LLM stop sequences list.

    Returns:
        Structured response dictionary with answer, sources, status, and diagnostic metrics.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")

    cleaned_q = question.strip()
    k_val = top_k if top_k is not None else settings.RETRIEVAL_TOP_K
    refusal_text = refusal_message or settings.SAFE_REFUSAL_MESSAGE

    # 1. Retrieve candidates if not pre-provided
    if chunks is not None:
        candidates = list(chunks)
    elif collection is not None:
        from src.retrieval.retriever import retrieve
        candidates = retrieve(query=cleaned_q, k=k_val, collection=collection)
    else:
        candidates = []

    # 2. Apply re-ranking if enabled
    rerank_enabled = use_reranker if use_reranker is not None else settings.RERANK_ENABLED
    if rerank_enabled and candidates:
        try:
            from src.retrieval.reranker import rerank
            candidates = rerank(
                query=cleaned_q,
                candidates=candidates,
                final_k=min(k_val, len(candidates)),
            )
        except Exception as exc:
            logger.warning("Re-ranking failed or bypassed (%s); continuing with initial candidates.", exc)

    # 3. Evaluate retrieval evidence strength
    eval_result = evaluate_retrieval_strength(
        chunks=candidates,
        min_top_score=min_top_score,
        min_supporting_chunks=min_supporting_chunks,
    )

    # 4. If retrieval is weak, refuse immediately WITHOUT calling the LLM
    if not eval_result["is_strong"]:
        logger.info(
            "Retrieval guardrail triggered (%s): top_score=%.4f (min=%.4f), supporting=%d (min=%d). Refusing without LLM call.",
            eval_result["status"],
            eval_result["top_score"],
            eval_result["min_top_score"],
            eval_result["supporting_chunks_count"],
            eval_result["min_supporting_chunks"],
        )
        return {
            "answer": refusal_text,
            "sources": [],
            "status": eval_result["status"],
            "refusal_reason": eval_result["refusal_reason"],
            "metrics": {
                "top_score": eval_result["top_score"],
                "supporting_chunks_count": eval_result["supporting_chunks_count"],
                "retrieved_chunks_count": eval_result["retrieved_chunks_count"],
                "min_top_score": eval_result["min_top_score"],
                "min_supporting_chunks": eval_result["min_supporting_chunks"],
                "llm_called": False,
            },
            "prompt_info": None,
            "context": None,
            "context_tokens": 0,
            "selected_chunks": [],
            "source_markers": [],
            "question": cleaned_q,
        }

    # 5. If retrieval is strong, proceed to context injection and LLM answer generation
    from src.services.llm import generate_grounded_answer

    llm_res = await generate_grounded_answer(
        question=cleaned_q,
        retrieved_chunks=candidates,
        system_instruction=system_instruction,
        max_context_tokens=max_context_tokens,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stop_sequences=stop_sequences,
    )

    return {
        "answer": llm_res["answer"],
        "sources": llm_res["sources_used"],
        "status": "answered",
        "refusal_reason": None,
        "metrics": {
            "top_score": eval_result["top_score"],
            "supporting_chunks_count": eval_result["supporting_chunks_count"],
            "retrieved_chunks_count": eval_result["retrieved_chunks_count"],
            "min_top_score": eval_result["min_top_score"],
            "min_supporting_chunks": eval_result["min_supporting_chunks"],
            "llm_called": True,
        },
        "prompt_info": llm_res.get("prompt_info"),
        "context": llm_res.get("context"),
        "context_tokens": llm_res.get("context_tokens", 0),
        "selected_chunks": llm_res.get("selected_chunks", []),
        "source_markers": llm_res.get("source_markers", []),
        "question": cleaned_q,
    }


def format_guardrail_report(result: Dict[str, Any]) -> str:
    """Format a sanitized diagnostic report of guardrail decisions and metrics.

    Args:
        result: Structured output dictionary from guarded_answer.

    Returns:
        Multi-line formatted summary string.
    """
    q = result.get("question", "")
    status = result.get("status", "unknown")
    metrics = result.get("metrics", {})
    sources = result.get("sources", [])
    reason = result.get("refusal_reason")

    lines = [
        "Retrieval Guardrail Diagnostic Report",
        "=" * 38,
        f"Question: {q}",
        f"Status: {status.upper()}",
        f"LLM Called: {metrics.get('llm_called', False)}",
        f"Top Retrieval Score: {metrics.get('top_score', 0.0):.4f} (Threshold: {metrics.get('min_top_score', 0.0):.4f})",
        f"Supporting Chunks: {metrics.get('supporting_chunks_count', 0)} (Required: {metrics.get('min_supporting_chunks', 0)})",
        f"Total Retrieved Chunks: {metrics.get('retrieved_chunks_count', 0)}",
    ]

    if reason:
        lines.append(f"Refusal Reason: {reason}")

    lines.extend([
        "",
        f"Sources Attributed: {len(sources)}",
    ])
    for s in sources:
        m = s.get("marker", "")
        src = s.get("source", "unknown")
        lines.append(f"  {m} {src}")

    lines.extend([
        "",
        "Answer / Response Text:",
        "-" * 25,
        result.get("answer", "").strip(),
    ])

    return "\n".join(lines)
