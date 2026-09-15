"""API route definitions and endpoints for documents, retrieval, and chat."""

from src.api.routes.admin import router as admin_router
from src.api.routes.auth import router as auth_router
from src.api.routes.conversations import router as conversations_router
from src.api.routes.documents import router as documents_router
from src.api.routes.query import router as query_router

__all__ = [
    "auth_router",
    "conversations_router",
    "documents_router",
    "query_router",
    "admin_router",
]

