"""Conversation and Chat Message Pydantic Data Models for finee.ai.

Defines schemas for MongoDB persistence, conversational RAG turns,
citations, evidence snippets, and conversation management.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageSource(BaseModel):
    """Retrieved evidence source / citation chunk attached to assistant message."""

    marker: str = Field(..., description="Citation marker (e.g. [1], [2])")
    source: str = Field(..., description="Document filename or title")
    document_id: Optional[str] = Field(default=None, description="Source document identifier")
    section: Optional[str] = Field(default=None, description="Document section or heading")
    page: Optional[int] = Field(default=1, description="Page number if applicable")
    approval_status: Optional[str] = Field(default="approved", description="Document regulatory approval state")
    effective_date: Optional[str] = Field(default=None, description="Policy effective date")
    version: Optional[str] = Field(default="1.0", description="Document version")
    text: str = Field(..., description="Extracted chunk excerpt text")
    relevance_score: Optional[float] = Field(default=None, description="Similarity or re-ranking score")
    is_direct_evidence: Optional[bool] = Field(default=False, description="Whether this is the primary direct evidence")


class RankedSnippet(BaseModel):
    """Ranked evidence snippet for right-sidebar inspector panel."""

    rank: int
    type: str = "Supporting Context"
    source: str
    section: str = "General Provisions"
    page: int = 1
    approval_status: str = "approved"
    score: float = 0.85
    text: str
    marker: str = "[1]"


class ChatMessage(BaseModel):
    """Individual message within a conversation."""

    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    role: str = Field(..., description="'user' | 'assistant' | 'system'")
    content: str = Field(..., description="Message text content")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )
    status: Optional[str] = Field(default="answered", description="'answered' | 'refused' | 'error' | 'pending'")
    refusal_reason: Optional[str] = None
    sources: List[ChatMessageSource] = Field(default_factory=list)
    ranked_snippets: List[RankedSnippet] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[Dict[str, Any]] = None
    pipeline_metrics: Optional[Dict[str, Any]] = None
    has_conflict: bool = False
    conflict_details: Optional[Dict[str, Any]] = None
    rewritten_query: Optional[str] = None


class Conversation(BaseModel):
    """Full persistent conversation model stored in MongoDB."""

    id: str = Field(default_factory=lambda: f"conv_{uuid.uuid4().hex[:16]}")
    user_id: str = Field(..., description="Owner user ID for strict multi-tenant isolation")
    title: str = Field(default="New Consultation", description="Human-readable conversation title")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_pinned: bool = Field(default=False, description="Whether conversation is pinned to sidebar top")
    messages: List[ChatMessage] = Field(default_factory=list)
    client_context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ConversationSummary(BaseModel):
    """Lightweight conversation summary for sidebar listings."""

    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    is_pinned: bool
    message_count: int
    last_message_preview: Optional[str] = None


class CreateConversationRequest(BaseModel):
    """Payload to create a new conversation."""

    title: Optional[str] = None
    client_context: Optional[Dict[str, Any]] = None
    initial_message: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Payload to send a message within an existing conversation."""

    message: str = Field(..., description="User query or prompt")
    client_context: Optional[Dict[str, Any]] = None
    k: Optional[int] = None
    use_reranker: Optional[bool] = None


class UpdateConversationRequest(BaseModel):
    """Payload to update conversation metadata (e.g. rename title)."""

    title: Optional[str] = None
    is_pinned: Optional[bool] = None


class PinToggleRequest(BaseModel):
    """Payload to toggle or explicitly set pinned status."""

    is_pinned: Optional[bool] = None
