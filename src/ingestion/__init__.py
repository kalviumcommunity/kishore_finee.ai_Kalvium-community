"""Document ingestion pipeline.

Responsible for document upload handling, text extraction, cleaning,
chunking strategies, and metadata processing.
"""

from .document_loader import load_text, load_documents
from .text_cleaner import clean_text, clean_documents
from .chunk_metadata import (
    create_chunk,
    get_source_reference,
    attach_metadata_to_chunks,
    Chunk,
    ChunkMetadata,
    VALID_APPROVAL_STATUSES,
)
from .chunking import (
    fixed_chunks,
    sentence_chunks,
    paragraph_chunks,
    recursive_chunks,
    chunk_document_with_metadata,
)

__all__ = [
    "load_text",
    "load_documents",
    "clean_text",
    "clean_documents",
    "create_chunk",
    "get_source_reference",
    "attach_metadata_to_chunks",
    "Chunk",
    "ChunkMetadata",
    "VALID_APPROVAL_STATUSES",
    "fixed_chunks",
    "sentence_chunks",
    "paragraph_chunks",
    "recursive_chunks",
    "chunk_document_with_metadata",
]

