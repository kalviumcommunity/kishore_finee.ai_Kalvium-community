"""Knowledge-base query and grounded search API routes for finee.ai."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.core.config import settings
from src.services.guardrails import guarded_answer
from src.vector_store.service import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """Request payload for RAG knowledge-base query."""

    query: Optional[str] = Field(default=None, description="User search query string")
    question: Optional[str] = Field(default=None, description="Alias for query")
    k: Optional[int] = Field(default=None, description="Top-k chunks to retrieve")
    min_top_score: Optional[float] = Field(default=None, description="Relevance guardrail score threshold")
    min_supporting_chunks: Optional[int] = Field(default=None, description="Minimum supporting chunks count")
    use_reranker: Optional[bool] = Field(default=None, description="Enable or bypass re-ranking")


class QueryResponse(BaseModel):
    """Structured response payload for RAG query."""

    answer: str
    sources: List[Dict[str, Any]]
    status: str
    refusal_reason: Optional[str] = None
    metrics: Dict[str, Any]
    question: str


@router.post(
    "",
    summary="Query Knowledge Base",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
)
async def query_knowledge_base(payload: QueryRequest) -> Dict[str, Any]:
    """Execute guarded similarity search and grounded answer generation across the active vector database.

    Dynamic runtime uploads are immediately searchable through this endpoint without restarting the app.
    """
    query_str = (payload.query or payload.question or "").strip()
    if not query_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string is required and cannot be empty.",
        )

    try:
        # Obtain collection from active Chroma vector store
        from src.retrieval.chroma_store import get_chroma_store
        chroma_store = get_chroma_store()

        result = await guarded_answer(
            question=query_str,
            collection=chroma_store,
            top_k=payload.k or settings.RETRIEVAL_TOP_K,
            min_top_score=payload.min_top_score,
            min_supporting_chunks=payload.min_supporting_chunks,
            use_reranker=payload.use_reranker,
        )

        return result
    except Exception as exc:
        logger.error("Query processing failed for '%s': %s", query_str, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error processing knowledge-base query.",
        )
