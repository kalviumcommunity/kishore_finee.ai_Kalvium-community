"""API route definitions and endpoints for documents, retrieval, and chat."""

from src.api.routes.documents import router as documents_router
from src.api.routes.query import router as query_router

__all__ = [
    "documents_router",
    "query_router",
]
