"""Unit and integration tests for FINEE.ai authentication and RBAC services."""

import pytest
from fastapi.testclient import TestClient

from src.core.config import settings
from src.main import app
from src.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

client = TestClient(app)


def test_password_hashing_and_verification():
    """Verify cryptographic PBKDF2 hashing and verification functions."""
    plain = "vaishnavi123"
    hashed = hash_password(plain)

    assert hashed.startswith("pbkdf2:sha256:100000$")
    assert verify_password(plain, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_creation_and_decoding():
    """Verify HS256 JWT token generation, payload preservation, and validation."""
    token = create_access_token(
        user_id="usr_test_123",
        email="test@finee.ai",
        role="ADMIN",
        name="Test Administrator",
        expires_delta_seconds=3600,
    )

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr_test_123"
    assert payload["email"] == "test@finee.ai"
    assert payload["role"] == "ADMIN"
    assert payload["name"] == "Test Administrator"


def test_jwt_tampered_token_rejection():
    """Verify tampered token signature rejection."""
    token = create_access_token(
        user_id="usr_test_123",
        email="test@finee.ai",
        role="USER",
        name="Test User",
    )
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}wrongsignature.{parts[2]}"

    assert decode_access_token(tampered_token) is None


def test_admin_login_success():
    """Verify administrator authentication with configured credentials."""
    response = client.post(
        "/auth/admin/login",
        json={
            "email": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["email"] == settings.ADMIN_EMAIL


def test_admin_login_invalid_password_rejected():
    """Verify rejected login with invalid administrator password (generic 401)."""
    response = client.post(
        "/auth/admin/login",
        json={
            "email": settings.ADMIN_EMAIL,
            "password": "wrong_password_attempt_99",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid administrator credentials."


def test_admin_login_unknown_email_rejected():
    """Verify rejected login with unknown admin email (generic 401, no enumeration)."""
    response = client.post(
        "/auth/admin/login",
        json={
            "email": "intruder@unknown-domain.com",
            "password": "vaishnavi123",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid administrator credentials."


def test_google_login_normal_user():
    """Verify Google OAuth login for normal advisory user gets USER role."""
    response = client.post(
        "/auth/google",
        json={
            "email": "advisor.john@apexwealth.com",
            "name": "John Doe",
            "firm": "Apex Wealth Management",
            "department": "Private Wealth",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "USER"
    assert data["user"]["email"] == "advisor.john@apexwealth.com"


def test_google_login_admin_email_gets_admin_role():
    """Verify Google OAuth login for configured admin email gets ADMIN role."""
    response = client.post(
        "/auth/google",
        json={
            "email": settings.ADMIN_EMAIL,
            "name": "Vaishnavi Pallempati",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["email"] == settings.ADMIN_EMAIL


def test_auth_me_endpoint():
    """Verify /auth/me returns identity when authenticated with Bearer token."""
    login_res = client.post(
        "/auth/admin/login",
        json={
            "email": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    token = login_res.json()["access_token"]

    me_res = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == settings.ADMIN_EMAIL
    assert me_data["role"] == "ADMIN"


def test_auth_me_unauthenticated_rejected():
    """Verify /auth/me rejects missing or invalid token with 401."""
    res = client.get("/auth/me")
    assert res.status_code == 401
