"""Unit and integration tests for FastAPI application endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.core.config import settings
from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient instance."""
    return TestClient(app)


def test_app_initialization():
    """Verify that the FastAPI application initializes with correct metadata."""
    assert app.title == "Compliance-Grounded Financial Advisory RAG Platform"
    assert app.version == "0.1.0"


def test_root_endpoint(client: TestClient):
    """Verify that GET / returns HTTP 200 and the expected status message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Financial Advisory RAG Platform API is running"
    }


def test_health_endpoint(client: TestClient):
    """Verify that GET /health returns HTTP 200, healthy status, and environment."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["environment"] == settings.APP_ENV


def test_documents_batch_upload_endpoint(client: TestClient):
    """Verify that POST /api/documents uploads documents into the Chroma vector store."""
    payload = {
        "ids": ["doc_test_1", "doc_test_2"],
        "documents": [
            "Marcus paid the advisory fee on 20 August.",
            "The mutual fund fact sheet outlines annual yield and expense ratio."
        ],
        "metadatas": [
            {"source": "payment_record.pdf", "category": "payment"},
            {"source": "factsheet.pdf", "category": "fund"}
        ]
    }
    response = client.post("/api/documents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Documents added successfully"
    assert data["count"] == 2

