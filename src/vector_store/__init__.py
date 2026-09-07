"""Vector store module for FInee.ai.

Provides vector database connectivity, collection management,
record upsert with text/metadata preservation, and readback verification.
"""

from src.vector_store.service import (
    DimensionMismatchError,
    InvalidRecordError,
    SchemaMismatchError,
    VectorRecord,
    VectorStoreError,
    VectorStoreService,
    generate_stable_id,
    get_vector_store,
)

__all__ = [
    "DimensionMismatchError",
    "InvalidRecordError",
    "SchemaMismatchError",
    "VectorRecord",
    "VectorStoreError",
    "VectorStoreService",
    "generate_stable_id",
    "get_vector_store",
]
