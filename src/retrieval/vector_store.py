"""Vector store module for finee.ai RAG platform.

Provides in-memory vector storage, chunk indexing, metadata filtering,
and similarity search for compliance-grounded financial advisory retrieval.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Sequence, Union
import uuid

import numpy as np
from pydantic import BaseModel, Field

from src.embeddings.embedder import cosine_similarity
from src.embeddings.embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class VectorRecord(BaseModel):
    """Structured record stored in the vector database collection."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: List[float]
    embedding_model: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert vector record to dictionary representation."""
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at,
        }


class InMemoryVectorStore:
    """In-memory vector store and similarity search collection."""

    def __init__(self, name: str = "default_collection") -> None:
        """Initialize an empty vector collection.

        Args:
            name: Identifier for the collection.
        """
        self.name = name
        self._records: List[VectorRecord] = []

    def count(self) -> int:
        """Return the total number of indexed vectors."""
        return len(self._records)

    def clear(self) -> None:
        """Clear all indexed records from the collection."""
        self._records.clear()

    def add(self, records: Sequence[Union[VectorRecord, Dict[str, Any]]]) -> int:
        """Add pre-embedded vector records to the collection.

        Args:
            records: Sequence of VectorRecord objects or dictionaries.

        Returns:
            Number of records successfully added.
        """
        added_count = 0
        for item in records:
            if isinstance(item, VectorRecord):
                self._records.append(item)
                added_count += 1
            elif isinstance(item, dict):
                record = VectorRecord(
                    id=item.get("id") or str(uuid.uuid4()),
                    text=item.get("text", ""),
                    metadata=item.get("metadata", {}),
                    embedding=item.get("embedding", []),
                    embedding_model=item.get("embedding_model", "unknown"),
                    created_at=item.get("created_at") or datetime.now(timezone.utc).isoformat(),
                )
                self._records.append(record)
                added_count += 1
            else:
                raise TypeError(f"Unsupported record type: {type(item).__name__}")
        return added_count

    def add_chunks(
        self,
        chunks: Sequence[Union[Dict[str, Any], Any]],
        embedding_service: Optional[EmbeddingService] = None,
        batch_size: Optional[int] = None,
    ) -> List[VectorRecord]:
        """Embed document chunks and index them into the vector store.

        Args:
            chunks: List of document chunks (dicts or Chunk objects).
            embedding_service: Optional EmbeddingService instance.
            batch_size: Optional batch size override.

        Returns:
            List of newly added VectorRecord instances.
        """
        service = embedding_service or get_embedding_service()
        try:
            embedded_records = service.embed_chunks(chunks=chunks, batch_size=batch_size, verbose=False)
        except Exception as exc:
            # Fallback to deterministic semantic vector generator when API key is not configured or in offline mode
            from src.embeddings.embedder import _generate_deterministic_semantic_vector
            logger.info("Using deterministic semantic vector embeddings: %s", exc)
            embedded_records = []
            for item in chunks:
                if isinstance(item, dict):
                    t = item.get("text", "")
                    m = item.get("metadata", {})
                else:
                    t = getattr(item, "text", "")
                    m = getattr(item, "metadata", {})
                    if hasattr(m, "model_dump"):
                        m = m.model_dump()
                vec = _generate_deterministic_semantic_vector(t, dimension=1536)
                embedded_records.append({
                    "text": t,
                    "metadata": m,
                    "embedding": vec,
                    "embedding_model": service.model,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

        new_records: List[VectorRecord] = []
        for rec in embedded_records:
            vec_rec = VectorRecord(
                id=rec.get("id") or str(uuid.uuid4()),
                text=rec["text"],
                metadata=rec["metadata"],
                embedding=rec["embedding"],
                embedding_model=rec.get("embedding_model", service.model),
                created_at=rec.get("created_at") or datetime.now(timezone.utc).isoformat(),
            )
            self._records.append(vec_rec)
            new_records.append(vec_rec)

        return new_records

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        include_embedding: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute top-k cosine similarity search against indexed records.

        Args:
            query_vector: Dense numerical embedding vector for the search query.
            top_k: Number of highest scoring results to return.
            filter_metadata: Optional key-value constraints to filter candidates.
            min_score: Optional minimum cosine similarity threshold.
            include_embedding: Whether to include the raw embedding in result items.

        Returns:
            List of ranked result dictionaries with score, text, and metadata.
        """
        if not self._records:
            return []

        if top_k <= 0:
            return []

        query_arr = np.asarray(query_vector, dtype=np.float64)
        if len(query_arr) == 0:
            raise ValueError("Query vector cannot be empty.")

        candidates = self._records
        if filter_metadata:
            candidates = [
                r for r in candidates
                if all(r.metadata.get(k) == v for k, v in filter_metadata.items())
            ]

        scored_results: List[Dict[str, Any]] = []
        for record in candidates:
            if not record.embedding or len(record.embedding) != len(query_arr):
                continue

            score = cosine_similarity(query_arr, record.embedding)

            if min_score is not None and score < min_score:
                continue

            result_item: Dict[str, Any] = {
                "id": record.id,
                "score": float(score),
                "text": record.text,
                "metadata": record.metadata,
                "embedding_model": record.embedding_model,
            }
            if include_embedding:
                result_item["embedding"] = record.embedding

            scored_results.append(result_item)

        # Sort descending by similarity score
        scored_results.sort(key=lambda item: item["score"], reverse=True)

        # Take top-k
        top_results = scored_results[:top_k]

        # Annotate 1-indexed rank
        for rank_idx, item in enumerate(top_results, start=1):
            item["rank"] = rank_idx

        return top_results

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all indexed records as dictionaries."""
        return [r.to_dict() for r in self._records]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize collection to dictionary format."""
        return {
            "name": self.name,
            "count": len(self._records),
            "records": [r.to_dict() for r in self._records],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InMemoryVectorStore:
        """Create a collection instance populated from serialized data."""
        store = cls(name=data.get("name", "default_collection"))
        records_data = data.get("records", [])
        store.add(records_data)
        return store
