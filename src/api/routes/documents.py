"""Document upload and indexing API routes for finee.ai."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.retrieval.chroma_store import get_chroma_store
from src.services.activity_tracker import get_activity_tracker
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


class DocumentDetailResponse(BaseModel):
    """Full detail model for document inspection view."""

    document_id: str
    original_filename: str
    stored_filename: str
    upload_timestamp: str
    status: str
    approval_status: str
    version: str = "1.0"
    file_size_bytes: int = 0
    content_type: Optional[str] = None
    chunks_count: int = 0
    chunks: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)


@router.post(
    "",
    summary="Upload and Index Document",
    response_model=DocumentSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (.txt, .md, .pdf, .html, .htm)"),
) -> Dict[str, Any]:
    """Upload a document, validate its format/size, extract/chunk/embed text, and dynamically index it."""
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

        # Record audit event
        get_activity_tracker().record_audit_event(
            actor="Marcus Vance (Advisor)",
            event_type="DOCUMENT_UPLOADED",
            description=f"Uploaded and indexed '{storage_meta['original_filename']}' ({indexing_res['summary']['chunks_indexed']} chunks).",
            status="SUCCESS",
            metadata={"document_id": storage_meta["document_id"], "filename": storage_meta["original_filename"]},
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
    tracker = get_status_tracker()
    docs = tracker.list_all()
    if not docs:
        # If tracker is empty, initialize records for existing upload files
        upload_dir = Path("./data/uploads")
        if upload_dir.exists():
            for f in sorted(upload_dir.glob("doc_*")):
                if f.is_file():
                    parts = f.name.split("_", 2)
                    doc_id = f"{parts[0]}_{parts[1]}" if len(parts) >= 2 else f.name
                    orig_name = parts[2] if len(parts) >= 3 else f.name
                    record = DocumentRecord(
                        document_id=doc_id,
                        original_filename=orig_name,
                        stored_filename=f.name,
                        file_size_bytes=f.stat().st_size,
                        status=DocumentStatus.INDEXED,
                        chunks_created=1,
                        chunks_indexed=1,
                        completed_at=datetime.now(timezone.utc).isoformat(),
                        metadata={"approval_status": "approved", "version": "1.0", "stored_path": str(f.resolve())},
                    )
                    tracker.register(record)
        docs = tracker.list_all()
    return docs


@router.get(
    "/{document_id}",
    summary="Get Document Detail & Chunks",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document_detail(document_id: str) -> Dict[str, Any]:
    """Retrieve detailed document metadata and chunk boundary previews for inspection."""
    record = get_status_tracker().get(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    # Fetch related chunks from Chroma vector store
    chroma_store = get_chroma_store()
    chunks: List[Dict[str, Any]] = []

    try:
        raw_data = chroma_store.collection.get(include=["documents", "metadatas"])
        if raw_data and raw_data.get("ids"):
            for idx, cid in enumerate(raw_data["ids"]):
                meta = raw_data["metadatas"][idx] if raw_data.get("metadatas") and idx < len(raw_data["metadatas"]) else {}
                doc_text = raw_data["documents"][idx] if raw_data.get("documents") and idx < len(raw_data["documents"]) else ""

                if (
                    meta.get("document_id") == document_id
                    or meta.get("source") == record.original_filename
                    or document_id in cid
                ):
                    chunks.append({
                        "id": cid,
                        "chunk_index": meta.get("chunk_index", len(chunks)),
                        "text": doc_text,
                        "section": meta.get("section", "Section " + str(len(chunks) + 1)),
                        "page": meta.get("page", 1),
                        "approval_status": meta.get("approval_status", "approved"),
                        "token_count": len(doc_text.split()),
                    })
    except Exception as exc:
        logger.warning("Error fetching chunks for document %s: %s", document_id, exc)

    # If no vector chunks found, read file content preview
    if not chunks:
        stored_path = record.metadata.get("stored_path")
        if stored_path and Path(stored_path).exists():
            try:
                from src.ingestion.document_loader import load_text
                from src.ingestion.chunking import recursive_chunks
                txt = load_text(stored_path)
                preview_chunks = recursive_chunks(txt, max_size=400)
                for i, c in enumerate(preview_chunks):
                    chunks.append({
                        "id": f"{document_id}:{i}",
                        "chunk_index": i,
                        "text": c,
                        "section": f"Section {i+1}",
                        "page": 1,
                        "approval_status": record.metadata.get("approval_status", "approved"),
                        "token_count": len(c.split()),
                    })
            except Exception:
                pass

    approval_status = record.metadata.get("approval_status", "approved")
    version = record.metadata.get("version", "1.0")

    timeline = [
        {"action": "Uploaded", "timestamp": record.upload_timestamp, "actor": "Marcus Vance", "status": "COMPLETED"},
        {"action": "Extraction & Semantic Chunking", "timestamp": record.upload_timestamp, "actor": "System Pipeline", "status": "COMPLETED"},
        {"action": "Vector Indexed (text-embedding-3-small)", "timestamp": record.completed_at or record.upload_timestamp, "actor": "ChromaDB Engine", "status": "COMPLETED"},
        {"action": "Compliance Approval", "timestamp": record.completed_at or record.upload_timestamp, "actor": "Elena Rostova (Compliance)", "status": "APPROVED" if approval_status == "approved" else "PENDING"},
    ]

    return {
        "document_id": record.document_id,
        "original_filename": record.original_filename,
        "stored_filename": record.stored_filename,
        "upload_timestamp": record.upload_timestamp,
        "status": getattr(record.status, "value", str(record.status)),
        "approval_status": approval_status,
        "version": version,
        "file_size_bytes": record.file_size_bytes,
        "content_type": record.content_type,
        "chunks_count": len(chunks),
        "chunks": chunks,
        "metadata": record.metadata,
        "timeline": timeline,
    }


@router.post("/{document_id}/approve", summary="Approve Document")
async def approve_document(document_id: str) -> Dict[str, Any]:
    """Approve a document for RAG retrieval."""
    tracker = get_status_tracker()
    record = tracker.get(document_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    tracker.update(document_id, approval_status="approved")
    get_activity_tracker().record_audit_event(
        actor="Elena Rostova (Compliance)",
        event_type="DOCUMENT_APPROVED",
        description=f"Approved policy document: '{record.original_filename}'.",
        status="SUCCESS",
        metadata={"document_id": document_id, "filename": record.original_filename},
    )
    return {"status": "success", "document_id": document_id, "approval_status": "approved"}


@router.post("/{document_id}/review", summary="Request Review for Document")
async def request_review_document(document_id: str) -> Dict[str, Any]:
    """Request compliance review for a document."""
    tracker = get_status_tracker()
    record = tracker.get(document_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    tracker.update(document_id, approval_status="review_requested")
    get_activity_tracker().record_audit_event(
        actor="Marcus Vance (Advisor)",
        event_type="DOCUMENT_REVIEW_REQUESTED",
        description=f"Review requested for document '{record.original_filename}'.",
        status="WARNING",
        metadata={"document_id": document_id, "filename": record.original_filename},
    )
    return {"status": "success", "document_id": document_id, "approval_status": "review_requested"}


@router.post("/{document_id}/archive", summary="Archive Document")
async def archive_document(document_id: str) -> Dict[str, Any]:
    """Archive a document and deprecate from active search."""
    tracker = get_status_tracker()
    record = tracker.get(document_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    tracker.update(document_id, approval_status="archived")
    get_activity_tracker().record_audit_event(
        actor="Elena Rostova (Compliance)",
        event_type="DOCUMENT_ARCHIVED",
        description=f"Archived document '{record.original_filename}'.",
        status="INFO",
        metadata={"document_id": document_id, "filename": record.original_filename},
    )
    return {"status": "success", "document_id": document_id, "approval_status": "archived"}
