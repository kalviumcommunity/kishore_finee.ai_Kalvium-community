"""Main entry point for FInee.ai FastAPI application.

Compliance-Grounded Financial Advisory RAG Platform.
"""

from fastapi import FastAPI
from src.core.config import settings

app = FastAPI(
    title="Compliance-Grounded Financial Advisory RAG Platform",
    description="Backend API for Compliance-Grounded Financial Advisory RAG Platform (FInee.ai)",
    version="0.1.0",
)


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
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.is_development,
    )
