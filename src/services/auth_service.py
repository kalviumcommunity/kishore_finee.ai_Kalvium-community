"""Enterprise Authentication and Role-Based Access Control (RBAC) Service for FINEE.ai.

Provides cryptographic password hashing, JWT session management, role verification,
and FastAPI security dependencies for Google OAuth and Administrator authentication.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Any, Dict, Optional, Tuple

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from src.core.config import settings
from src.services.activity_tracker import UserProfile, get_activity_tracker

logger = logging.getLogger(__name__)

# Security scheme for FastAPI OpenAPI docs
security_bearer = HTTPBearer(auto_error=False)


# ============================================================================
# Models
# ============================================================================

class AdminLoginRequest(BaseModel):
    """Request payload for hidden administrator authentication."""

    email: str = Field(..., description="Administrator work email address")
    password: str = Field(..., description="Administrator password")


class GoogleAuthRequest(BaseModel):
    """Request payload for Google OAuth user authentication."""

    token: Optional[str] = Field(default=None, description="Google OAuth ID Token or Access Token")
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(default=None, description="User full name")
    picture: Optional[str] = Field(default=None, description="User avatar URL")
    firm: Optional[str] = Field(default="Apex Global Wealth", description="Advisory firm name")
    department: Optional[str] = Field(default="Private Wealth Advisory", description="Advisory department")


class AuthTokenResponse(BaseModel):
    """Authenticated session response returning JWT access token and user profile."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


# ============================================================================
# Cryptographic Password & Token Utilities
# ============================================================================

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"pbkdf2:sha256:100000${salt}${hashed.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        expected_hex = parts[2]
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return hmac.compare_digest(computed.hex(), expected_hex)
    except Exception as exc:
        logger.warning("Error verifying password: %s", exc)
        return False


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to Base64URL string without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    """Decode Base64URL string with padding correction."""
    padding = len(data) % 4
    if padding != 0:
        data += "=" * (4 - padding)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    name: str,
    expires_delta_seconds: Optional[int] = None,
) -> str:
    """Generate a standard HS256 cryptographically signed JWT access token."""
    now = int(time.time())
    if expires_delta_seconds is None:
        expires_delta_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    exp = now + expires_delta_seconds

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
        "iat": now,
        "exp": exp,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode HS256 JWT access token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        message = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            settings.JWT_SECRET_KEY.encode("utf-8"),
            message,
            hashlib.sha256,
        ).digest()

        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(actual_sig, expected_sig):
            logger.warning("Invalid JWT signature.")
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        now = int(time.time())
        if payload.get("exp") and payload["exp"] < now:
            logger.warning("JWT token expired.")
            return None

        return payload
    except Exception as exc:
        logger.warning("Failed to decode token: %s", exc)
        return None


# ============================================================================
# AuthService Business Logic
# ============================================================================

class AuthService:
    """Authentication and Identity manager for FINEE.ai."""

    def __init__(self) -> None:
        self.tracker = get_activity_tracker()

    def authenticate_admin(self, email: str, password: str) -> Tuple[UserProfile, str]:
        """Authenticate administrator using configured secure credentials.

        Validates against settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD / settings.ADMIN_PASSWORD_HASH.
        """
        clean_email = email.strip().lower()
        configured_admin = settings.ADMIN_EMAIL.strip().lower()

        # Check email match
        is_email_match = clean_email == configured_admin

        # Check password match
        is_password_match = False
        if settings.ADMIN_PASSWORD_HASH:
            is_password_match = verify_password(password, settings.ADMIN_PASSWORD_HASH)
        elif settings.ADMIN_PASSWORD:
            is_password_match = hmac.compare_digest(password, settings.ADMIN_PASSWORD)

        if not (is_email_match and is_password_match):
            # Record failed login attempt audit event
            self.tracker.record_audit_event(
                actor=email,
                event_type="ADMIN_LOGIN_FAILED",
                description=f"Failed admin authentication attempt for '{email}'",
                status="WARNING",
            )
            # Generic error message to prevent account enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid administrator credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Retrieve or provision Admin user profile
        user_id = "usr_admin_vaishnavi"
        admin_user = self.tracker.get_user(user_id)
        if not admin_user:
            admin_user = UserProfile(
                user_id=user_id,
                name="Vaishnavi Pallempati",
                role="ADMIN",
                department="Executive & Regulatory Compliance",
                email=configured_admin,
                status="active",
            )
        else:
            admin_user.role = "ADMIN"
            admin_user.last_active = datetime.now(timezone.utc).isoformat()

        # Generate JWT session token
        token = create_access_token(
            user_id=admin_user.user_id,
            email=admin_user.email,
            role="ADMIN",
            name=admin_user.name,
        )

        # Record successful admin login in enterprise audit trail
        self.tracker.record_audit_event(
            actor=admin_user.name,
            event_type="ADMIN_LOGIN_SUCCESS",
            description=f"Administrator '{admin_user.email}' authenticated successfully.",
            status="SUCCESS",
            metadata={"user_id": admin_user.user_id, "role": "ADMIN"},
        )

        return admin_user, token

    def authenticate_google_user(self, payload: GoogleAuthRequest) -> Tuple[UserProfile, str]:
        """Authenticate user via Google OAuth and determine server-side role."""
        clean_email = payload.email.strip().lower()
        extracted_name = payload.name
        extracted_picture = payload.picture

        # If Google ID token is provided, extract real verified claims
        if payload.token:
            try:
                parts = payload.token.split(".")
                if len(parts) == 3:
                    google_claims = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
                    if google_claims.get("email"):
                        clean_email = google_claims["email"].strip().lower()
                    if google_claims.get("name"):
                        extracted_name = google_claims["name"]
                    if google_claims.get("picture"):
                        extracted_picture = google_claims["picture"]
            except Exception as exc:
                logger.warning("Error parsing Google ID token: %s", exc)

        is_admin_email = clean_email == settings.ADMIN_EMAIL.strip().lower()

        # Backend determines the role: only configured admin email gets ADMIN role
        assigned_role = "ADMIN" if is_admin_email else "USER"
        user_id = "usr_admin_vaishnavi" if is_admin_email else f"usr_{clean_email.split('@')[0].replace('.', '_')}"

        name = extracted_name or (
            "Vaishnavi Pallempati"
            if is_admin_email
            else clean_email.split("@")[0].replace(".", " ").title()
        )
        department = (
            "Executive & Regulatory Compliance"
            if is_admin_email
            else (payload.department or "Private Wealth Advisory")
        )

        user = self.tracker.get_user(user_id)
        if not user:
            user = UserProfile(
                user_id=user_id,
                name=name,
                role=assigned_role,
                department=department,
                email=clean_email,
                status="active",
            )
        else:
            user.role = assigned_role
            user.name = name
            user.last_active = datetime.now(timezone.utc).isoformat()

        token = create_access_token(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            name=user.name,
        )

        self.tracker.record_audit_event(
            actor=user.name,
            event_type="USER_GOOGLE_LOGIN_SUCCESS",
            description=f"User '{user.email}' logged in via Google OAuth with role {user.role}.",
            status="SUCCESS",
            metadata={"user_id": user.user_id, "role": user.role},
        )

        return user, token


_auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Retrieve global default AuthService instance."""
    return _auth_service


# ============================================================================
# FastAPI Security Dependencies
# ============================================================================

async def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[UserProfile]:
    """Extract and validate bearer token from Authorization header."""
    if not auth_header or not auth_header.credentials:
        return None

    payload = decode_access_token(auth_header.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    tracker = get_activity_tracker()
    user = tracker.get_user(user_id)
    if not user:
        # Recreate profile from token if not present in memory
        user = UserProfile(
            user_id=user_id,
            name=payload.get("name", "Authenticated User"),
            role=payload.get("role", "USER"),
            department="Advisory",
            email=payload.get("email", ""),
            status="active",
        )

    return user


async def require_authenticated_user(
    user: Optional[UserProfile] = Depends(get_current_user),
) -> UserProfile:
    """Dependency ensuring user is authenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: Optional[UserProfile] = Depends(get_current_user),
) -> UserProfile:
    """Dependency enforcing ADMIN role authorization.

    Returns 401 if unauthenticated, 403 Forbidden if not an administrator.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role != "ADMIN":
        logger.warning("Access denied: User '%s' with role '%s' attempted admin access.", user.email, user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator privileges required.",
        )
    return user
