"""Vector database store service and readback verification for finee.ai.

Provides a provider-agnostic vector store abstraction wrapping Chroma,
enforcing vector dimension constraints, cosine distance metric, stable IDs,
and co-locating embeddings with text and metadata.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
from pydantic import BaseModel, Field

from src.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Base exception for vector database operations."""
    pass


class DimensionMismatchError(VectorStoreError):
    """Raised when an embedding vector length does not match the configured collection dimension."""
    pass


class SchemaMismatchError(VectorStoreError):
    """Raised when collection configuration or metadata violates expected schema."""
    pass


class InvalidRecordError(VectorStoreError):
    """Raised when a chunk record is malformed or contains invalid vector data."""
    pass


class VectorRecord(BaseModel):
    """Data representation of a vector record stored in the vector database."""

    id: str
    vector: List[float]
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "id": self.id,
            "vector": self.vector,
            "text": self.text,
            "metadata": self.metadata,
            "embedding_model": self.embedding_model,
        }


def generate_stable_id(record: Union[Dict[str, Any], Any]) -> str:
    """Generate a deterministic, stable chunk identifier.

    Format: document_id:chunk_index (or source:chunk_index).

    Args:
        record: Chunk record dictionary or object.

    Returns:
        Stable string identifier.
    """
    if isinstance(record, dict):
        if "id" in record and record["id"]:
            return str(record["id"])

        metadata = record.get("metadata", {})
        doc_id = metadata.get("document_id") or metadata.get("source", "doc")
        chunk_idx = metadata.get("chunk_index", 0)
        return f"{doc_id}:{chunk_idx}"

    if hasattr(record, "id") and getattr(record, "id"):
        return str(getattr(record, "id"))

    if hasattr(record, "metadata"):
        meta = record.metadata
        if isinstance(meta, dict):
            doc_id = meta.get("document_id") or meta.get("source", "doc")
            chunk_idx = meta.get("chunk_index", 0)
        else:
            doc_id = getattr(meta, "document_id", None) or getattr(meta, "source", "doc")
            chunk_idx = getattr(meta, "chunk_index", 0)
        return f"{doc_id}:{chunk_idx}"

    return "doc:0"


def _clean_metadata_for_chroma(metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool]]:
    """Ensure all metadata dictionary values are primitive types supported by Chroma."""
    cleaned: Dict[str, Union[str, int, float, bool]] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = json.dumps(value)
    return cleaned


class VectorStoreService:
    """Provider-agnostic vector database service managing collection lifecycle and upsert/readback."""

    def __init__(
        self,
        db_type: Optional[str] = None,
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
        distance_metric: Optional[str] = None,
        persist_path: Optional[str] = None,
        in_memory: bool = False,
        client: Optional[Any] = None,
    ) -> None:
        """Initialize vector store service with configuration parameters.

        Args:
            db_type: Vector DB type ('chroma', 'memory').
            collection_name: Target collection name (default: settings.VECTOR_COLLECTION_NAME).
            dimension: Expected vector dimension (default: settings.VECTOR_DIMENSION).
            distance_metric: Distance metric ('cosine', 'l2', 'ip').
            persist_path: Local persistence directory path.
            in_memory: If True, uses ephemeral in-memory client.
            client: Optional pre-configured Chroma client instance.
        """
        self.db_type = (db_type or settings.VECTOR_DB_TYPE).lower()
        self.collection_name = collection_name or settings.VECTOR_COLLECTION_NAME
        self.dimension = dimension or settings.VECTOR_DIMENSION
        self.distance_metric = (distance_metric or settings.VECTOR_DISTANCE_METRIC).lower()
        self.persist_path = persist_path or settings.VECTOR_DB_PATH
        self.in_memory = in_memory or (self.db_type == "memory")
        self._client = client
        self._collection = None

    def connect(self) -> Any:
        """Connect to vector database backend."""
        if self._client is not None:
            return self._client

        try:
            import chromadb

            if self.in_memory:
                self._client = chromadb.EphemeralClient()
            else:
                abs_path = str(Path(self.persist_path).resolve())
                os.makedirs(abs_path, exist_ok=True)
                self._client = chromadb.PersistentClient(path=abs_path)

            return self._client
        except Exception as exc:
            raise VectorStoreError(f"Failed to connect to vector database ({self.db_type}): {exc}") from exc

    def get_or_create_collection(self, collection_name: Optional[str] = None) -> Any:
        """Retrieve or create the vector collection with specified distance metric.

        Args:
            collection_name: Optional collection name override.

        Returns:
            Chroma Collection object.
        """
        target_name = collection_name or self.collection_name
        client = self.connect()

        # Map distance metric to Chroma HNSW space configuration
        space_mapping = {
            "cosine": "cosine",
            "l2": "l2",
            "ip": "ip",
        }
        hnsw_space = space_mapping.get(self.distance_metric, "cosine")

        try:
            self._collection = client.get_or_create_collection(
                name=target_name,
                metadata={
                    "hnsw:space": hnsw_space,
                    "dimension": self.dimension,
                },
            )

            # Validate existing collection metadata space if present
            if self._collection.metadata:
                col_space = self._collection.metadata.get("hnsw:space")
                if col_space and col_space != hnsw_space:
                    raise SchemaMismatchError(
                        f"Collection '{target_name}' exists with metric '{col_space}', "
                        f"expected '{hnsw_space}'."
                    )

            return self._collection
        except SchemaMismatchError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"Failed to get or create collection '{target_name}': {exc}") from exc

    def validate_vector(self, vector: Any, record_id: str = "") -> List[float]:
        """Validate embedding vector for presence, numeric float type, non-emptiness, and dimension.

        Args:
            vector: Embedding vector sequence to validate.
            record_id: Contextual record identifier for error messages.

        Returns:
            Validated list of float values.

        Raises:
            InvalidRecordError: If vector is empty, non-numeric, or contains NaN/Inf.
            DimensionMismatchError: If vector dimension does not match configured dimension.
        """
        if vector is None:
            raise InvalidRecordError(f"Record '{record_id}' is missing embedding vector.")

        if not isinstance(vector, (list, tuple, np.ndarray)):
            raise InvalidRecordError(f"Vector for '{record_id}' must be a list/sequence, got {type(vector).__name__}.")

        if len(vector) == 0:
            raise InvalidRecordError(f"Vector for '{record_id}' cannot be empty.")

        if len(vector) != self.dimension:
            raise DimensionMismatchError(
                f"Vector dimension mismatch for '{record_id}': expected {self.dimension}, got {len(vector)}."
            )

        try:
            arr = np.asarray(vector, dtype=np.float64)
        except (ValueError, TypeError) as err:
            raise InvalidRecordError(f"Vector for '{record_id}' contains non-numeric values: {err}") from err

        if not np.all(np.isfinite(arr)):
            raise InvalidRecordError(f"Vector for '{record_id}' contains NaN or infinite values.")

        return arr.tolist()

    def upsert_records(
        self,
        records: Sequence[Union[Dict[str, Any], Any]],
        collection_name: Optional[str] = None,
    ) -> List[str]:
        """Insert or update chunk records in the vector database.

        Args:
            records: Sequence of chunk records (dicts, VectorRecord, or Chunk objects).
            collection_name: Optional collection name override.

        Returns:
            List of upserted stable IDs.
        """
        if not records:
            return []

        collection = self.get_or_create_collection(collection_name)

        ids: List[str] = []
        embeddings: List[List[float]] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for idx, rec in enumerate(records):
            rec_id = generate_stable_id(rec)

            if isinstance(rec, dict):
                text = rec.get("text", "")
                raw_vec = rec.get("embedding") or rec.get("vector")
                meta = rec.get("metadata", {})
                model = rec.get("embedding_model")
            elif hasattr(rec, "text") and hasattr(rec, "metadata"):
                text = rec.text
                raw_vec = getattr(rec, "embedding", None) or getattr(rec, "vector", None)
                meta = rec.metadata if isinstance(rec.metadata, dict) else rec.metadata.model_dump()
                model = getattr(rec, "embedding_model", None)
            else:
                raise InvalidRecordError(f"Invalid record format at index {idx}.")

            if not isinstance(text, str) or not text:
                raise InvalidRecordError(f"Record '{rec_id}' has invalid or empty text content.")

            valid_vec = self.validate_vector(raw_vec, record_id=rec_id)

            cleaned_meta = _clean_metadata_for_chroma(meta)
            if model:
                cleaned_meta["embedding_model"] = model

            ids.append(rec_id)
            embeddings.append(valid_vec)
            documents.append(text)
            metadatas.append(cleaned_meta)

        try:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            return ids
        except Exception as exc:
            raise VectorStoreError(f"Failed to upsert {len(ids)} records: {exc}") from exc

    def upsert_record(
        self,
        record: Union[Dict[str, Any], Any],
        collection_name: Optional[str] = None,
    ) -> str:
        """Upsert a single chunk record."""
        ids = self.upsert_records([record], collection_name=collection_name)
        return ids[0]

    def get_record_by_id(
        self,
        record_id: str,
        collection_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a stored vector record by its ID with text, metadata, and embedding.

        Args:
            record_id: Stable identifier of the chunk record.
            collection_name: Optional collection name override.

        Returns:
            Dictionary containing record data, or None if not found.
        """
        collection = self.get_or_create_collection(collection_name)

        try:
            result = collection.get(
                ids=[record_id],
                include=["embeddings", "documents", "metadatas"],
            )

            if not result or not result["ids"] or len(result["ids"]) == 0:
                return None

            ret_id = result["ids"][0]
            ret_doc = result["documents"][0] if result["documents"] else ""
            ret_meta = result["metadatas"][0] if result["metadatas"] else {}
            ret_vec = result["embeddings"][0] if result["embeddings"] is not None else None

            # Handle ndarray embedding return format from Chroma
            if isinstance(ret_vec, np.ndarray):
                ret_vec = ret_vec.tolist()

            return {
                "id": ret_id,
                "text": ret_doc,
                "metadata": ret_meta,
                "vector": ret_vec,
                "embedding_dimension": len(ret_vec) if ret_vec else 0,
            }
        except Exception as exc:
            raise VectorStoreError(f"Failed to read record '{record_id}': {exc}") from exc

    def count(self, collection_name: Optional[str] = None) -> int:
        """Return the number of records in the collection."""
        collection = self.get_or_create_collection(collection_name)
        return collection.count()

    def delete_record_by_id(self, record_id: str, collection_name: Optional[str] = None) -> None:
        """Delete a record by ID."""
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=[record_id])

    def verify_insert_and_readback(
        self,
        test_record: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute end-to-end insert and readback verification.

        Args:
            test_record: Optional custom test record dictionary.

        Returns:
            Dictionary containing verification statistics and check results.
        """
        # Default test record if none provided
        if test_record is None:
            # Generate deterministic mock vector of the configured dimension
            mock_vec = [float(i % 100) / 100.0 for i in range(self.dimension)]
            test_record = {
                "id": "account-guide.md:0",
                "text": "Marcus paid the advisory fee on 20 August. The transaction was verified.",
                "metadata": {
                    "source": "account-guide.md",
                    "document_id": "account-guide.md",
                    "document_version": "1.0",
                    "chunk_index": 0,
                    "page": 2,
                    "section": "Payment History",
                    "approval_status": "approved",
                },
                "embedding": mock_vec,
                "embedding_model": "text-embedding-3-small",
            }

        expected_id = generate_stable_id(test_record)
        expected_text = test_record.get("text", "")
        expected_meta = test_record.get("metadata", {})

        # 1. Connect & setup collection
        self.get_or_create_collection()

        # 2. Upsert record
        inserted_id = self.upsert_record(test_record)

        # 3. Readback record
        readback = self.get_record_by_id(inserted_id)

        if not readback:
            return {
                "collection": self.collection_name,
                "dimension": self.dimension,
                "metric": self.distance_metric,
                "inserted_id": inserted_id,
                "readback_id": None,
                "vector_length": 0,
                "text_preserved": False,
                "metadata_preserved": False,
                "dimension_valid": False,
                "readback_successful": False,
                "error": f"Record '{inserted_id}' was not found upon readback.",
            }

        # 4. Compare fields
        readback_id = readback["id"]
        readback_text = readback["text"]
        readback_meta = readback["metadata"]
        readback_vec = readback["vector"]
        vec_len = len(readback_vec) if readback_vec else 0

        id_match = (readback_id == inserted_id)
        text_match = (readback_text == expected_text)
        dim_match = (vec_len == self.dimension)

        # Compare core metadata attributes
        meta_match = all(
            readback_meta.get(k) == v
            for k, v in expected_meta.items()
            if isinstance(v, (str, int, float, bool))
        )

        readback_success = bool(id_match and text_match and dim_match and meta_match)

        return {
            "collection": self.collection_name,
            "dimension": self.dimension,
            "metric": self.distance_metric,
            "inserted_id": inserted_id,
            "readback_id": readback_id,
            "vector_length": vec_len,
            "text_preserved": text_match,
            "metadata_preserved": meta_match,
            "dimension_valid": dim_match,
            "readback_successful": readback_success,
        }

    def generate_verification_report(self, result: Dict[str, Any]) -> str:
        """Format a clean, human-readable vector store verification report."""
        col = result.get("collection", self.collection_name)
        dim = result.get("dimension", self.dimension)
        metric = result.get("metric", self.distance_metric)
        ins_id = result.get("inserted_id", "N/A")
        rb_id = result.get("readback_id", "N/A")
        vec_len = result.get("vector_length", 0)
        txt_pass = "PASS" if result.get("text_preserved") else "FAIL"
        meta_pass = "PASS" if result.get("metadata_preserved") else "FAIL"
        dim_pass = "PASS" if result.get("dimension_valid") else "FAIL"
        success_pass = "PASS" if result.get("readback_successful") else "FAIL"

        lines = [
            "Vector Store Verification",
            "=" * 25,
            f"Collection: {col}",
            f"Dimension: {dim}",
            f"Metric: {metric}",
            "",
            f"Inserted ID: {ins_id}",
            f"Readback ID: {rb_id}",
            f"Vector length: {vec_len}",
            f"Text preserved: {txt_pass}",
            f"Metadata preserved: {meta_pass}",
            f"Dimension valid: {dim_pass}",
            f"Readback successful: {success_pass}",
        ]
        return "\n".join(lines)


# Global singleton instance
_default_vector_store: Optional[VectorStoreService] = None


def get_vector_store(in_memory: bool = False) -> VectorStoreService:
    """Retrieve or create the global default VectorStoreService instance."""
    global _default_vector_store
    if _default_vector_store is None:
        _default_vector_store = VectorStoreService(in_memory=in_memory)
    return _default_vector_store


def main() -> None:
    """CLI entry point for vector store setup and readback verification."""
    print("=" * 60)
    print("FInee.ai - VECTOR DATABASE SETUP & VERIFICATION")
    print("=" * 60)

    service = get_vector_store()
    print(f"Vector DB Engine : {service.db_type}")
    print(f"Collection Name  : {service.collection_name}")
    print(f"Dimension        : {service.dimension}")
    print(f"Distance Metric  : {service.distance_metric}")
    print(f"Persist Path     : {service.persist_path}")
    print("-" * 60)

    try:
        result = service.verify_insert_and_readback()
        report = service.generate_verification_report(result)
        print("\n" + report)
    except Exception as exc:
        print(f"\nVerification Failed: {exc}")


if __name__ == "__main__":
    main()
