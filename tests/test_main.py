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
