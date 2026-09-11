"""Comprehensive Unit and Integration Tests for MongoDB Chat Persistence, Chat History, and Pinned Conversations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest

from src.core.config import settings
from src.db.mongodb import InMemoryConversationCollection, MongoDBManager, get_mongodb_manager
from src.main import app
from src.models.conversation import (
    ChatMessage,
    ChatMessageSource,
    Conversation,
    ConversationSummary,
    CreateConversationRequest,
    PinToggleRequest,
    RankedSnippet,
    SendMessageRequest,
    UpdateConversationRequest,
)
from src.services.activity_tracker import UserProfile
from src.services.auth_service import create_access_token
from src.services.conversation_service import ConversationService, get_conversation_service


@pytest.fixture
def client() -> TestClient:
    """FastAPI Test Client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure conversation storage is clean before each test."""
    service = get_conversation_service()
    if hasattr(service.collection, "delete_many"):
        service.collection.delete_many({})
    elif hasattr(service.collection, "clear"):
        service.collection.clear()
    yield
    if hasattr(service.collection, "delete_many"):
        service.collection.delete_many({})
    elif hasattr(service.collection, "clear"):
        service.collection.clear()


@pytest.fixture
def advisor_token() -> str:
    """Generate JWT for standard advisor user."""
    return create_access_token(
        user_id="usr_advisor_john",
        email="john.advisor@apexwealth.com",
        role="USER",
        name="John Advisor",
    )


@pytest.fixture
def admin_token() -> str:
    """Generate JWT for administrator user."""
    return create_access_token(
        user_id="usr_admin_vaishnavi",
        email=settings.ADMIN_EMAIL,
        role="ADMIN",
        name="Vaishnavi Pallempati",
    )


# ============================================================================
# 1. In-Memory Collection & Database Unit Tests
# ============================================================================

def test_in_memory_collection_crud():
    """Verify in-memory fallback collection handles full CRUD lifecycle correctly."""
    col = InMemoryConversationCollection()
    assert col.count_documents({}) == 0

    # Insert
    doc1 = {"_id": "conv_1", "user_id": "u1", "title": "SEBI Compliance", "is_pinned": False, "updated_at": "2026-01-01T10:00:00Z"}
    doc2 = {"_id": "conv_2", "user_id": "u1", "title": "Portfolio Limits", "is_pinned": True, "updated_at": "2026-01-02T10:00:00Z"}
    doc3 = {"_id": "conv_3", "user_id": "u2", "title": "Other User Chat", "is_pinned": False, "updated_at": "2026-01-03T10:00:00Z"}

    col.insert_one(doc1)
    col.insert_one(doc2)
    col.insert_one(doc3)

    assert col.count_documents({}) == 3
    assert col.count_documents({"user_id": "u1"}) == 2

    # Find one
    found = col.find_one({"_id": "conv_1"})
    assert found is not None
    assert found["title"] == "SEBI Compliance"

    # Find with sort (pinned first, then updated_at desc)
    results = col.find({"user_id": "u1"}, sort=[("is_pinned", -1), ("updated_at", -1)])
    assert len(results) == 2
    assert results[0]["_id"] == "conv_2"  # Pinned is first
    assert results[1]["_id"] == "conv_1"

    # Update
    col.update_one({"_id": "conv_1"}, {"$set": {"title": "Updated Title"}})
    updated = col.find_one({"_id": "conv_1"})
    assert updated["title"] == "Updated Title"

    # Delete
    col.delete_one({"_id": "conv_1"})
    assert col.count_documents({"user_id": "u1"}) == 1
    assert col.find_one({"_id": "conv_1"}) is None


# ============================================================================
# 2. ConversationService Business Logic Unit Tests
# ============================================================================

def test_create_and_get_conversation():
    """Verify creating a conversation and retrieving it with user isolation."""
    service = get_conversation_service()
    user_id = "usr_test_123"

    conv = service.create_conversation(
        user_id=user_id,
        title="Institutional Fiduciary Analysis",
        client_context={"client": "Acme Capital", "tier": "Tier 1"},
    )

    assert conv.id.startswith("conv_")
    assert conv.user_id == user_id
    assert conv.title == "Institutional Fiduciary Analysis"
    assert conv.is_pinned is False
    assert len(conv.messages) == 0

    # Retrieve by owner
    fetched = service.get_conversation(conv.id, user_id=user_id)
    assert fetched is not None
    assert fetched.id == conv.id
    assert fetched.client_context["client"] == "Acme Capital"

    # Retrieve by another user must return None (Multi-tenant isolation!)
    unauthorized_fetch = service.get_conversation(conv.id, user_id="usr_intruder_999")
    assert unauthorized_fetch is None


def test_toggle_pin_and_sorting():
    """Verify pinning conversations moves them to top of conversation summaries."""
    service = get_conversation_service()
    user_id = "usr_advisor_sorting"

    conv1 = service.create_conversation(user_id=user_id, title="Chat 1 Alpha")
    conv2 = service.create_conversation(user_id=user_id, title="Chat 2 Beta")
    conv3 = service.create_conversation(user_id=user_id, title="Chat 3 Gamma")

    # Initial order: latest created first
    summaries = service.get_conversations(user_id=user_id)
    assert len(summaries) == 3

    # Pin conv1
    service.toggle_pin(conv1.id, user_id=user_id, is_pinned=True)

    summaries = service.get_conversations(user_id=user_id)
    assert summaries[0].id == conv1.id
    assert summaries[0].is_pinned is True

    # Unpin conv1
    service.toggle_pin(conv1.id, user_id=user_id, is_pinned=False)
    summaries = service.get_conversations(user_id=user_id)
    assert summaries[0].is_pinned is False


def test_delete_conversation():
    """Verify deleting conversation permanently removes it for the user."""
    service = get_conversation_service()
    user_id = "usr_delete_tester"

    conv = service.create_conversation(user_id=user_id, title="To Be Deleted")
    assert service.get_conversation(conv.id, user_id=user_id) is not None

    deleted = service.delete_conversation(conv.id, user_id=user_id)
    assert deleted is True
    assert service.get_conversation(conv.id, user_id=user_id) is None

    # Delete non-existent or unauthorized returns False
    assert service.delete_conversation("conv_nonexistent", user_id=user_id) is False


import asyncio


def test_execute_chat_turn_persists_rag():
    """Verify full chat turn records user question and assistant grounded answer with sources."""
    service = get_conversation_service()
    user_id = "usr_turn_tester"

    conv = service.create_conversation(user_id=user_id, title="New Consultation")

    with patch("src.services.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "SEBI guidelines require mandatory risk disclosures on all promotional materials [1]."

        user_msg, assistant_msg = asyncio.run(
            service.execute_chat_turn(
                conversation_id=conv.id,
                user_id=user_id,
                question="What are SEBI's advertising risk disclosure rules?",
            )
        )

        assert user_msg.role == "user"
        assert "SEBI" in user_msg.content

        assert assistant_msg.role == "assistant"
        assert assistant_msg.status == "answered"
        assert "SEBI guidelines require" in assistant_msg.content
        assert len(assistant_msg.sources) >= 1
        assert assistant_msg.usage is not None

        # Verify conversation updated in storage
        updated_conv = service.get_conversation(conv.id, user_id=user_id)
        assert len(updated_conv.messages) == 2
        assert updated_conv.messages[0].content == user_msg.content
        assert updated_conv.messages[1].content == assistant_msg.content
        assert "SEBI" in updated_conv.title  # Auto-generated title


# ============================================================================
# 3. FastAPI REST Endpoints Integration Tests
# ============================================================================

def test_api_list_conversations_empty(client: TestClient, advisor_token: str):
    """Verify GET /conversations returns empty list when user has zero chats."""
    headers = {"Authorization": f"Bearer {advisor_token}"}
    res = client.get("/conversations", headers=headers)
    assert res.status_code == 200
    assert res.json() == []


def test_api_create_and_list_conversations(client: TestClient, advisor_token: str):
    """Verify POST /conversations creates a conversation and GET /conversations lists it."""
    headers = {"Authorization": f"Bearer {advisor_token}"}

    payload = {
        "title": "Private Wealth Structuring",
        "client_context": {"client": "Vertex Partners"},
    }
    create_res = client.post("/conversations", json=payload, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["title"] == "Private Wealth Structuring"
    conv_id = created_data["id"]

    # List conversations
    list_res = client.get("/conversations", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == conv_id
    assert items[0]["title"] == "Private Wealth Structuring"
    assert items[0]["is_pinned"] is False


def test_api_get_conversation_by_id(client: TestClient, advisor_token: str):
    """Verify GET /conversations/{id} returns full conversation."""
    headers = {"Authorization": f"Bearer {advisor_token}"}

    create_res = client.post(
        "/conversations",
        json={"title": "Compliance Review 2026"},
        headers=headers,
    )
    conv_id = create_res.json()["id"]

    get_res = client.get(f"/conversations/{conv_id}", headers=headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == conv_id
    assert data["title"] == "Compliance Review 2026"
    assert data["messages"] == []


def test_api_send_message_in_conversation(client: TestClient, advisor_token: str):
    """Verify POST /conversations/{id}/messages executes RAG and returns assistant response."""
    headers = {"Authorization": f"Bearer {advisor_token}"}

    create_res = client.post("/conversations", json={}, headers=headers)
    conv_id = create_res.json()["id"]

    with patch("src.services.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Under AIF regulations, sponsor commitment must remain at minimum 2.5% of corpus [1]."

        msg_payload = {"message": "What is the minimum sponsor commitment under AIF guidelines?"}
        msg_res = client.post(f"/conversations/{conv_id}/messages", json=msg_payload, headers=headers)

        assert msg_res.status_code == 200
        data = msg_res.json()
        assert data["conversation_id"] == conv_id
        assert "AIF regulations" in data["answer"]
        assert len(data["sources"]) >= 1
        assert data["status"] == "answered"
        assert len(data["ranked_snippets"]) >= 1
        assert len(data["audit_trail"]) >= 1

        # Check conversation history has 2 messages
        conv_res = client.get(f"/conversations/{conv_id}", headers=headers)
        assert len(conv_res.json()["messages"]) == 2


def test_api_toggle_pin(client: TestClient, advisor_token: str):
    """Verify PATCH /conversations/{id}/pin toggles pinned status."""
    headers = {"Authorization": f"Bearer {advisor_token}"}

    create_res = client.post("/conversations", json={"title": "High Priority Chat"}, headers=headers)
    conv_id = create_res.json()["id"]
    assert create_res.json()["is_pinned"] is False

    # Pin
    pin_res = client.patch(f"/conversations/{conv_id}/pin", json={"is_pinned": True}, headers=headers)
    assert pin_res.status_code == 200
    assert pin_res.json()["is_pinned"] is True

    # Unpin
    unpin_res = client.patch(f"/conversations/{conv_id}/pin", json={"is_pinned": False}, headers=headers)
    assert unpin_res.status_code == 200
    assert unpin_res.json()["is_pinned"] is False


def test_api_update_conversation_title(client: TestClient, advisor_token: str):
    """Verify PATCH /conversations/{id} renames title."""
    headers = {"Authorization": f"Bearer {advisor_token}"}

    create_res = client.post("/conversations", json={"title": "Old Name"}, headers=headers)
    conv_id = create_res.json()["id"]

    patch_res = client.patch(f"/conversations/{conv_id}", json={"title": "Renamed Consultation"}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Renamed Consultation"


def test_api_delete_conversation(client: TestClient, advisor_token: str):
    """Verify DELETE /conversations/{id} deletes conversation."""
    headers = {"Authorization": f"Bearer {advisor_token}"}

    create_res = client.post("/conversations", json={"title": "Temporary Chat"}, headers=headers)
    conv_id = create_res.json()["id"]

    del_res = client.delete(f"/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Confirm 404
    get_res = client.get(f"/conversations/{conv_id}", headers=headers)
    assert get_res.status_code == 404
