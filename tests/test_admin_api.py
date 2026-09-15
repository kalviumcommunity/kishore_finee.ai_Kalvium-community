"""Tests for Admin API routes, observability, and activity tracking."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.activity_tracker import get_activity_tracker
from src.services.document_upload import get_status_tracker

client = TestClient(app)


def test_cors_headers_configured():
    """Verify that CORS middleware is active and allows requests."""
    response = client.options(
        "/query",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ["http://localhost:3000", "*"]


def test_admin_overview_endpoint():
    """Verify GET /admin/overview returns real dashboard statistics and recent activity."""
    response = client.get("/admin/overview")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "recent_documents" in data
    assert "activity_timeline" in data
    stats = data["stats"]
    assert "total_queries" in stats
    assert "approved_documents" in stats
    assert "system_status" in stats


def test_admin_knowledge_base_metrics():
    """Verify GET /admin/knowledge-base returns infrastructure health and chunk list."""
    response = client.get("/admin/knowledge-base")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "pipeline_stages" in data
    assert "corpus_health" in data
    assert "chunks" in data
    assert isinstance(data["chunks"], list)
    assert len(data["pipeline_stages"]) >= 5


def test_admin_test_retrieval_endpoint():
    """Verify POST /admin/test-retrieval executes retrieval diagnostic search."""
    response = client.post(
        "/admin/test-retrieval",
        json={
            "query": "advisory fee and suitability requirements",
            "top_k": 3,
            "use_reranker": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "advisory fee and suitability requirements"
    assert "status" in data
    assert "top_score" in data
    assert "chunks" in data
    assert "latency_ms" in data


def test_admin_activity_log():
    """Verify GET /admin/activity returns audit event log."""
    response = client.get("/admin/activity?limit=10")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) > 0
    assert "actor" in events[0]
    assert "event_type" in events[0]


def test_admin_users_and_activity():
    """Verify GET /admin/users and GET /admin/users/{user_id}/activity."""
    users_resp = client.get("/admin/users")
    assert users_resp.status_code == 200
    users = users_resp.json()
    assert isinstance(users, list)
    assert len(users) >= 1
    user_id = users[0]["user_id"]

    act_resp = client.get(f"/admin/users/{user_id}/activity")
    assert act_resp.status_code == 200
    act_data = act_resp.json()
    assert "user" in act_data
    assert "token_summary" in act_data


def test_admin_token_usage_analytics():
    """Verify GET /admin/token-usage returns aggregate token metrics."""
    response = client.get("/admin/token-usage")
    assert response.status_code == 200
    data = response.json()
    assert "total_prompt_tokens" in data
    assert "total_completion_tokens" in data
    assert "total_cost_usd" in data
    assert "models" in data


def test_admin_settings():
    """Verify GET /admin/settings returns system configuration."""
    response = client.get("/admin/settings")
    assert response.status_code == 200
    data = response.json()
    assert "MIN_TOP_SCORE" in data
    assert "RETRIEVAL_TOP_K" in data
    assert "EMBEDDING_MODEL" in data


def test_document_lifecycle_actions():
    """Verify document lifecycle actions: approve, review, archive."""
    list_resp = client.get("/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    if not docs:
        pytest.skip("No documents in tracker")

    doc_id = docs[0]["document_id"]

    # Detail
    detail_resp = client.get(f"/documents/{doc_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["document_id"] == doc_id
    assert "chunks" in detail_data

    # Approve
    app_resp = client.post(f"/documents/{doc_id}/approve")
    assert app_resp.status_code == 200
    assert app_resp.json()["approval_status"] == "approved"

    # Review
    rev_resp = client.post(f"/documents/{doc_id}/review")
    assert rev_resp.status_code == 200
    assert rev_resp.json()["approval_status"] == "review_requested"

    # Archive
    arc_resp = client.post(f"/documents/{doc_id}/archive")
    assert arc_resp.status_code == 200
    assert arc_resp.json()["approval_status"] == "archived"


@patch("src.services.llm.generate_grounded_answer")
def test_query_endpoint_with_conversational_history(mock_grounded):
    """Verify POST /query returns full payload with usage, pipeline metrics, and citations."""
    mock_grounded.return_value = {
        "answer": "The client suitability policy mandates risk profiling prior to executing discretionary trades [1].",
        "prompt_info": {"context": "mock", "system_instruction": "mock", "question": "mock"},
        "context": "Context snippet [1]",
        "context_tokens": 120,
        "selected_chunks": [
            {
                "text": "The client suitability policy mandates risk profiling.",
                "score": 0.92,
                "metadata": {"source": "suitability-policy.md", "section": "Section 2.1", "page": 1, "approval_status": "approved"},
            }
        ],
        "sources_used": [
            {
                "marker": "[1]",
                "source": "suitability-policy.md",
                "text": "The client suitability policy mandates risk profiling.",
                "score": 0.92,
                "metadata": {"source": "suitability-policy.md", "section": "Section 2.1", "page": 1, "approval_status": "approved"},
            }
        ],
        "source_markers": ["[1]"],
    }

    response = client.post(
        "/query",
        json={
            "query": "What is the policy on client suitability?",
            "user_id": "usr_marcus_vance",
            "client_context": {
                "entity_name": "Apex Wealth Fund",
                "entity_id": "APX-901",
                "risk_tier": "Tier 1",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "pipeline_metrics" in data
    assert "usage" in data
    assert "ranked_snippets" in data
    assert "audit_trail" in data
