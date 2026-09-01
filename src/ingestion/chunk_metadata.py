"""Chunk metadata models and source tracking helpers for finee.ai."""

from pathlib import Path
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


def find_char_positions(text: str, chunks: list[str]) -> list[Optional[int]]:
    """
    Find the starting character position of each chunk within the source text.

    Args:
        text: The full source text.
        chunks: List of chunk text strings.

    Returns:
        List of integer starting positions (or None if not found).
    """
    results = []
    search_start = 0

    for chunk in chunks:
        position = text.find(chunk, search_start)
        if position != -1:
            results.append(position)
            search_start = position + len(chunk)
        else:
            results.append(None)

    return results


def create_chunk_metadata(
    source: str,
    chunks: list[str],
    positions: Optional[list[Optional[int]]] = None,
) -> list[dict[str, Any]]:
    """
    Attach source and position metadata to a list of chunks.

    Args:
        source: Source document identifier.
        chunks: List of chunk text strings.
        positions: Optional list of starting character positions.

    Returns:
        List of chunk dictionaries with metadata.
    """
    documents = []

    for index, chunk in enumerate(chunks):
        pos = positions[index] if positions and index < len(positions) else None
        char_end = pos + len(chunk) if pos is not None else None
        documents.append(
            create_chunk(
                text=chunk,
                source=source,
                chunk_index=index,
                char_start=pos,
                char_end=char_end,
            )
        )

    return documents


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
    positions = find_char_positions(full_text, chunks) if full_text is not None else None
    result = []

    for idx, chunk_text in enumerate(chunks):
        char_start = positions[idx] if positions is not None else None
        char_end = char_start + len(chunk_text) if char_start is not None else None

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


def main() -> None:
    """Demonstrate chunk metadata and source tracking across sample documents."""
    from src.ingestion.document_loader import load_text
    from src.ingestion.chunking import recursive_chunks

    data_dir = Path("data")

    print("=" * 60)
    print("FInee.ai - CHUNK METADATA & SOURCE TRACKING")
    print("=" * 60)

    total_chunks = 0

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue

        if path.suffix.lower() not in [
            ".pdf",
            ".txt",
            ".md",
            ".html",
            ".htm",
        ]:
            continue

        try:
            # Load document
            text = load_text(path)

            if not text.strip():
                continue

            # Recursive chunking
            chunks = recursive_chunks(text, max_size=150)

            # Find starting character positions
            positions = find_char_positions(text, chunks)

            # Attach metadata
            documents = []
            for index, (chunk, position) in enumerate(zip(chunks, positions)):
                char_end = position + len(chunk) if position is not None else None
                documents.append(
                    create_chunk(
                        text=chunk,
                        source=path.name,
                        chunk_index=index,
                        char_start=position,
                        char_end=char_end,
                    )
                )

            print("\n" + "-" * 60)
            print(f"Document: {path.name}")
            print(f"Chunks  : {len(documents)}")
            print("-" * 60)

            # Display first few chunks
            for item in documents[:3]:
                print(f"\nChunk {item['metadata']['chunk_index']}")
                print(f"Source     : {item['metadata']['source']}")
                print(f"Char start : {item['metadata']['char_start']}")
                print(f"Text       : {item['text'][:120]}")

            total_chunks += len(documents)

        except Exception as error:
            print(f"Could not process {path.name}: {error}")

    print("\n" + "=" * 60)
    print("METADATA SUMMARY")
    print("=" * 60)
    print(f"Total chunks with metadata: {total_chunks}")
    print("Every chunk contains:")
    print("  - source")
    print("  - chunk_index")
    print("  - char_start")
    print("=" * 60)


if __name__ == "__main__":
    main()
