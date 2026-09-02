"""Chunk metadata models and source tracking helpers for finee.ai."""

from typing import Any, Optional
from pydantic import BaseModel, Field


VALID_APPROVAL_STATUSES = {
    "draft",
    "processing",
    "pending_approval",
    "approved",
    "superseded",
    "archived",
}


class ChunkMetadata(BaseModel):
    """Metadata attributes associated with a document chunk."""

    source: str
    document_id: Optional[str] = None
    document_version: Optional[str] = None
    chunk_index: int = 0
    page: Optional[int] = None
    section: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    effective_date: Optional[str] = None
    approval_status: Optional[str] = None


class Chunk(BaseModel):
    """Document chunk containing text and associated metadata."""

    text: str
    metadata: ChunkMetadata

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk model to standard dictionary format."""
        return {
            "text": self.text,
            "metadata": self.metadata.model_dump(),
        }


def create_chunk(
    text: str,
    source: str,
    document_id: Optional[str] = None,
    document_version: Optional[str] = None,
    chunk_index: int = 0,
    page: Optional[int] = None,
    section: Optional[str] = None,
    char_start: Optional[int] = None,
    char_end: Optional[int] = None,
    effective_date: Optional[str] = None,
    approval_status: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a standardized chunk dictionary containing text and metadata.

    Args:
        text: The text content of the chunk.
        source: Mandatory identifier of the source document (e.g. filename).
        document_id: Optional unique identifier of the source document.
        document_version: Optional document version string (e.g. '1.0', '3.2').
        chunk_index: Position index of the chunk within the document.
        page: Optional page number where chunk occurs.
        section: Optional section heading/name.
        char_start: Optional starting character index in the source text.
        char_end: Optional ending character index in the source text.
        effective_date: Optional document effective date (e.g. '2026-08-20').
        approval_status: Optional approval lifecycle status.

    Returns:
        A dictionary in the format {"text": ..., "metadata": {...}}.
    """
    if not source or not str(source).strip():
        raise ValueError("source is required for chunk creation")

    metadata = {
        "source": source,
        "document_id": document_id,
        "document_version": document_version,
        "chunk_index": chunk_index,
        "page": page,
        "section": section,
        "char_start": char_start,
        "char_end": char_end,
        "effective_date": effective_date,
        "approval_status": approval_status,
    }

    return {
        "text": text,
        "metadata": metadata,
    }


def get_source_reference(chunk: dict | Any) -> str:
    """
    Generate a human-readable traceability citation reference for a chunk.

    Args:
        chunk: A chunk dictionary or Chunk object containing metadata.

    Returns:
        Formatted string detailing source document, version, page, section, and chunk index.
    """
    if isinstance(chunk, dict) and "metadata" in chunk:
        meta = chunk["metadata"]
    elif isinstance(chunk, dict):
        meta = chunk
    elif hasattr(chunk, "metadata"):
        meta = chunk.metadata if isinstance(chunk.metadata, dict) else chunk.metadata.model_dump()
    elif hasattr(chunk, "model_dump"):
        meta = chunk.model_dump()
    else:
        raise ValueError("Invalid chunk format")

    parts = []
    if meta.get("source"):
        parts.append(f"Source:\n{meta['source']}")
    if meta.get("document_version"):
        parts.append(f"Version:\n{meta['document_version']}")
    if meta.get("page") is not None:
        parts.append(f"Page:\n{meta['page']}")
    if meta.get("section"):
        parts.append(f"Section:\n{meta['section']}")
    if meta.get("chunk_index") is not None:
        parts.append(f"Chunk:\n{meta['chunk_index']}")
    if meta.get("approval_status"):
        parts.append(f"Status:\n{meta['approval_status']}")
    if meta.get("effective_date"):
        parts.append(f"Effective Date:\n{meta['effective_date']}")
    if meta.get("document_id"):
        parts.append(f"Document ID:\n{meta['document_id']}")

    return "\n\n".join(parts)


def attach_metadata_to_chunks(
    chunks: list[str],
    source: str,
    document_id: Optional[str] = None,
    document_version: Optional[str] = None,
    page: Optional[int] = None,
    section: Optional[str] = None,
    effective_date: Optional[str] = None,
    approval_status: Optional[str] = None,
    full_text: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Attach consistent metadata to a list of chunk texts.

    Args:
        chunks: List of raw chunk strings.
        source: Source document identifier.
        document_id: Optional document ID.
        document_version: Optional document version.
        page: Optional page number.
        section: Optional section name.
        effective_date: Optional document effective date.
        approval_status: Optional approval status.
        full_text: Optional full document text used to compute char_start and char_end.

    Returns:
        List of structured chunk dictionaries with metadata.
    """
    result = []
    cursor = 0

    for idx, chunk_text in enumerate(chunks):
        char_start = None
        char_end = None

        if full_text is not None:
            found_pos = full_text.find(chunk_text, cursor)
            if found_pos != -1:
                char_start = found_pos
                char_end = found_pos + len(chunk_text)
                cursor = char_end

        chunk_dict = create_chunk(
            text=chunk_text,
            source=source,
            document_id=document_id,
            document_version=document_version,
            chunk_index=idx,
            page=page,
            section=section,
            char_start=char_start,
            char_end=char_end,
            effective_date=effective_date,
            approval_status=approval_status,
        )
        result.append(chunk_dict)

    return result
