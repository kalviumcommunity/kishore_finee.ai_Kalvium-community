"""Documents router for batch document upload into Chroma vector store."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.vector_store.service import get_vector_store

router = APIRouter()


class AddDocumentRequest(BaseModel):
    """Request schema for batch document ingestion."""

    documents: List[str]
    ids: Optional[List[str]] = None
    metadatas: Optional[List[Dict[str, Any]]] = None
    embeddings: Optional[List[List[float]]] = None


@router.post("", summary="Batch upload documents to Chroma", status_code=status.HTTP_200_OK)
@router.post("/", summary="Batch upload documents to Chroma (trailing slash)", status_code=status.HTTP_200_OK, include_in_schema=False)
async def add_documents_endpoint(payload: AddDocumentRequest) -> Dict[str, Any]:
    """Upload documents in batches to the configured Chroma collection."""
    try:
        store = get_vector_store()
        result = store.add_documents(
            documents=payload.documents,
            ids=payload.ids,
            metadatas=payload.metadatas,
            embeddings=payload.embeddings,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add documents to Chroma collection: {exc}",
        ) from exc
