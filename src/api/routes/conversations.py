"""Conversation and Chat History API routes for finee.ai.

Provides RESTful endpoints for multi-turn chat sessions, conversation listings,
message persistence in MongoDB, pinning/unpinning, and conversational RAG orchestration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.models.conversation import (
    ChatMessage,
    Conversation,
    ConversationSummary,
    CreateConversationRequest,
    PinToggleRequest,
    SendMessageRequest,
    UpdateConversationRequest,
)
from src.services.activity_tracker import UserProfile
from src.services.auth_service import get_current_user
from src.services.conversation_service import get_conversation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _resolve_user_id(current_user: Optional[UserProfile]) -> str:
    """Extract authenticated user ID or fallback to standard default advisor ID."""
    if current_user and current_user.user_id:
        return current_user.user_id
    return "usr_advisor_default"


@router.get(
    "",
    summary="List User Conversations",
    response_model=List[ConversationSummary],
    status_code=status.HTTP_200_OK,
)
async def list_conversations(
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> List[ConversationSummary]:
    """Retrieve all conversations belonging to the authenticated user, sorted pinned first then updated_at descending."""
    user_id = _resolve_user_id(current_user)
    service = get_conversation_service()
    return service.get_conversations(user_id=user_id)


@router.post(
    "",
    summary="Create New Conversation",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: CreateConversationRequest,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Conversation:
    """Create a new persistent conversation for the authenticated user."""
    user_id = _resolve_user_id(current_user)
    service = get_conversation_service()
    return service.create_conversation(
        user_id=user_id,
        title=payload.title,
        client_context=payload.client_context,
        initial_message=payload.initial_message,
    )


@router.get(
    "/{conversation_id}",
    summary="Get Conversation Details",
    response_model=Conversation,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: str,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Conversation:
    """Retrieve full conversation details including messages, citations, and evidence snippets."""
    user_id = _resolve_user_id(current_user)
    service = get_conversation_service()
    conv = service.get_conversation(conversation_id=conversation_id, user_id=user_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or access denied.",
        )
    return conv


@router.post(
    "/{conversation_id}/messages",
    summary="Send Message in Conversation",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
)
async def send_message(
    conversation_id: str,
    payload: SendMessageRequest,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Submit a question to a conversation, run grounded Conversational RAG, and persist turn in MongoDB."""
    question = payload.message.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty.",
        )

    user_id = _resolve_user_id(current_user)
    service = get_conversation_service()

    user_msg, assistant_msg = await service.execute_chat_turn(
        conversation_id=conversation_id,
        user_id=user_id,
        question=question,
        client_context=payload.client_context,
        k=payload.k,
        use_reranker=payload.use_reranker,
    )

    return {
        "conversation_id": conversation_id,
        "user_message": user_msg.model_dump(),
        "assistant_message": assistant_msg.model_dump(),
        # Also return root fields for direct UI compatibility
        "answer": assistant_msg.content,
        "sources": [s.model_dump() for s in assistant_msg.sources],
        "status": assistant_msg.status,
        "refusal_reason": assistant_msg.refusal_reason,
        "ranked_snippets": [s.model_dump() for s in assistant_msg.ranked_snippets],
        "audit_trail": assistant_msg.audit_trail,
        "usage": assistant_msg.usage,
        "pipeline_metrics": assistant_msg.pipeline_metrics,
        "has_conflict": assistant_msg.has_conflict,
        "conflict_details": assistant_msg.conflict_details,
        "rewritten_query": assistant_msg.rewritten_query,
    }


@router.patch(
    "/{conversation_id}/pin",
    summary="Toggle Pinned State",
    response_model=Conversation,
    status_code=status.HTTP_200_OK,
)
async def toggle_pin(
    conversation_id: str,
    payload: Optional[PinToggleRequest] = None,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Conversation:
    """Toggle or update the is_pinned status of a conversation."""
    user_id = _resolve_user_id(current_user)
    service = get_conversation_service()
    is_pinned_val = payload.is_pinned if payload else None
    conv = service.toggle_pin(conversation_id=conversation_id, user_id=user_id, is_pinned=is_pinned_val)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or access denied.",
        )
    return conv


@router.patch(
    "/{conversation_id}",
    summary="Update Conversation Metadata",
    response_model=Conversation,
    status_code=status.HTTP_200_OK,
)
async def update_conversation(
    conversation_id: str,
    payload: UpdateConversationRequest,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Conversation:
    """Update conversation properties like title or pinned status."""
    user_id = _resolve_user_id(current_user)
    service = get_conversation_service()

    conv = service.get_conversation(conversation_id, user_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or access denied.",
        )

    if payload.title is not None:
        conv = service.update_title(conversation_id, user_id, payload.title)
    if payload.is_pinned is not None:
        conv = service.toggle_pin(conversation_id, user_id, payload.is_pinned)

    return conv  # type: ignore


@router.delete(
    "/{conversation_id}",
    summary="Delete Conversation",
    status_code=status.HTTP_200_OK,
)
async def delete_conversation(
    conversation_id: str,
    current_user: Optional[UserProfile] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Permanently delete a conversation and its messages from MongoDB."""
    user_id = _resolve_user_id(current_user)
    service = get_conversation_service()
    deleted = service.delete_conversation(conversation_id=conversation_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or unauthorized.",
        )
    return {"status": "deleted", "conversation_id": conversation_id}
