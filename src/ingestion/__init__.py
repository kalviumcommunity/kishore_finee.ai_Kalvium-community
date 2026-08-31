"""Document ingestion pipeline.

Responsible for document upload handling, text extraction, cleaning,
chunking strategies, and metadata processing.
"""

from .document_loader import load_text, load_documents
from .text_cleaner import clean_text, clean_documents

__all__ = ["load_text", "load_documents", "clean_text", "clean_documents"]
