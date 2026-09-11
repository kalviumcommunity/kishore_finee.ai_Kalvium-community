"""Main entry point for FINEE.ai FastAPI application.

Compliance-Grounded Financial Advisory RAG Platform with Role-Based Authentication.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.admin import router as admin_router
from src.api.routes.auth import router as auth_router
from src.api.routes.conversations import router as conversations_router
from src.api.routes.documents import router as documents_router
from src.api.routes.query import router as query_router
from src.core.config import settings

app = FastAPI(
    title="Compliance-Grounded Financial Advisory RAG Platform",
    description="Backend API for Compliance-Grounded Financial Advisory RAG Platform with Role-Based Access Control",
    version="0.1.0",
)

# Enable CORS for frontend Next.js application
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3005",
        "http://127.0.0.1:3005",
        "http://localhost:3006",
        "http://127.0.0.1:3006",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register sub-routers
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(admin_router)


@app.get("/", summary="Root Endpoint")
async def root() -> dict[str, str]:
    """Root endpoint returning API status message."""
    return {"message": "Financial Advisory RAG Platform API is running"}


@app.get("/health", summary="Health Check")
async def health_check() -> dict[str, str]:
    """Health check endpoint returning system status and current environment."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "platform": "FINEE.ai Knowledge Control",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.is_development,
    )
