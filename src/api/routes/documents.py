"""Document upload and indexing API routes for finee.ai."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.services.document_upload import (
    DocumentRecord,
    DocumentStatus,
    DocumentUploadError,
    EmptyDocumentError,
    EmptyFileError,
    ExtractionError,
    FileOversizedError,
    IndexingError,
    InvalidFilenameError,
    UnsupportedFileTypeError,
    get_status_tracker,
    process_uploaded_document,
    store_upload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentSummaryResponse(BaseModel):
    """Response model for document upload and indexing."""

    status: str
    document_id: str
    filename: str
    summary: Dict[str, int]


@router.post(
    "",
    summary="Upload and Index Document",
    response_model=DocumentSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (.txt, .md, .pdf, .html, .htm)"),
) -> Dict[str, Any]:
    """Upload a document, validate its format/size, extract/chunk/embed text, and dynamically index it.

    Supported formats: .txt, .md, .pdf, .html, .htm

    Flow:
      1. Validate file extension and size.
      2. Store file safely to avoid path traversal and collision.
      3. Process document through text extraction, cleaning, chunking, metadata tagging.
      4. Generate embeddings and upsert into the active vector database collection.
      5. Return structured indexing summary without requiring application restart.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required and cannot be empty.",
        )

    # 1. Safely store the uploaded file
    try:
        storage_meta = await store_upload(file)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    except FileOversizedError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except (EmptyFileError, InvalidFilenameError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except DocumentUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error during file upload storage: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store uploaded file safely.",
        )

    # 2. Ingest and index document into the vector database
    try:
        indexing_res = await process_uploaded_document(
            path=storage_meta["stored_path"],
            document_id=storage_meta["document_id"],
            original_filename=storage_meta["original_filename"],
        )
        return indexing_res
    except (EmptyDocumentError, ExtractionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except (IndexingError, DocumentUploadError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error during document ingestion/indexing: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document indexing.",
        )


@router.get(
    "",
    summary="List Tracked Documents",
    response_model=List[DocumentRecord],
    status_code=status.HTTP_200_OK,
)
async def list_documents() -> List[DocumentRecord]:
    """Retrieve list of all tracked uploaded documents and their processing status."""
    return get_status_tracker().list_all()


@router.get(
    "/{document_id}",
    summary="Get Document Status",
    response_model=DocumentRecord,
    status_code=status.HTTP_200_OK,
)
async def get_document_status(document_id: str) -> DocumentRecord:
    """Retrieve current processing status and metadata for a specific document ID."""
    record = get_status_tracker().get(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return record
