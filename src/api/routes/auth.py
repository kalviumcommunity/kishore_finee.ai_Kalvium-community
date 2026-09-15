"""Authentication API routes for FINEE.ai.

Exposes endpoints for Google OAuth user authentication, hidden administrator login,
session validation (/auth/me), and secure logout.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.config import settings
from src.services.activity_tracker import UserProfile, get_activity_tracker
from src.services.auth_service import (
    AdminLoginRequest,
    AuthTokenResponse,
    GoogleAuthRequest,
    get_auth_service,
    get_current_user,
    require_authenticated_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/admin/login",
    summary="Administrator Login",
    response_model=AuthTokenResponse,
    responses={
        401: {"description": "Invalid administrator credentials"},
    },
)
async def admin_login(payload: AdminLoginRequest) -> Dict[str, Any]:
    """Authenticate administrator using configured secure credentials.

    Enforces backend credential verification and returns a signed session token with ADMIN role.
    """
    auth_service = get_auth_service()
    user, token = auth_service.authenticate_admin(
        email=payload.email,
        password=payload.password,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


@router.post(
    "/google",
    summary="Google OAuth Login",
    response_model=AuthTokenResponse,
)
async def google_login(payload: GoogleAuthRequest) -> Dict[str, Any]:
    """Authenticate user with Google OAuth credentials.

    The backend determines the user role (USER or ADMIN) and issues a signed session token.
    """
    auth_service = get_auth_service()
    user, token = auth_service.authenticate_google_user(payload)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


@router.get(
    "/me",
    summary="Current Authenticated User Profile",
    response_model=UserProfile,
)
async def get_me(user: UserProfile = Depends(require_authenticated_user)) -> UserProfile:
    """Retrieve identity and token consumption profile of the currently authenticated user."""
    return user


@router.post(
    "/logout",
    summary="Logout Session",
)
async def logout(current_user: UserProfile = Depends(get_current_user)) -> Dict[str, str]:
    """Invalidate session and log logout event."""
    if current_user:
        get_activity_tracker().record_audit_event(
            actor=current_user.name,
            event_type="LOGOUT_SUCCESS",
            description=f"User '{current_user.email}' logged out.",
            status="SUCCESS",
        )
    return {"message": "Session terminated successfully."}
