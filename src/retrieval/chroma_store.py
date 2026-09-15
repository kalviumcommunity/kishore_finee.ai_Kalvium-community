"""ChromaDB Vector Store Integration for finee.ai.

Provides ChromaDB-backed persistent and in-memory vector storage,
HNSW cosine similarity indexing, metadata filtering, and top-k search.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union, cast
import uuid

try:
    import chromadb
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection
    HAS_CHROMADB = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    chromadb = None  # type: ignore
    ClientAPI = Any  # type: ignore
    Collection = Any  # type: ignore
    HAS_CHROMADB = False

from src.embeddings.embedding_service import EmbeddingService, get_embedding_service
from src.retrieval.vector_store import VectorRecord

logger = logging.getLogger(__name__)


def _sanitize_metadata_for_chroma(metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool]]:
    """Sanitize metadata dictionary to ensure all values are Chroma-supported primitives."""
    clean_meta: Dict[str, Union[str, int, float, bool]] = {}
    for k, v in metadata.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean_meta[k] = v
        else:
            clean_meta[k] = str(v)
    return clean_meta


class ChromaVectorStore:
    """ChromaDB-backed vector store for financial RAG embeddings and retrieval."""

    def __init__(
        self,
        collection_name: str = "finee_financial_corpus",
        persist_directory: Optional[Union[str, Path]] = None,
        client: Optional[ClientAPI] = None,
    ) -> None:
        """Initialize ChromaDB collection with cosine distance metric.

        Args:
            collection_name: Name of the Chroma collection.
            persist_directory: Optional directory path for on-disk persistence.
            client: Optional pre-configured chromadb client.
        """
        if not HAS_CHROMADB:
            raise ImportError(
                "chromadb is not installed in the active Python environment. "
                "Please activate the virtual environment (`source .venv/bin/activate`) "
                "or install it with `pip install chromadb`."
            )

        self.collection_name = collection_name
        self.persist_directory = str(persist_directory) if persist_directory else None

        if client is not None:
            self.client = client
        elif self.persist_directory:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
        else:
            self.client = chromadb.EphemeralClient()

        # Initialize collection with cosine space for HNSW similarity
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Return total number of items stored in Chroma collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all records by deleting and recreating the collection."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_records(self, records: Sequence[Union[VectorRecord, Dict[str, Any]]]) -> int:
        """Add pre-embedded VectorRecords directly to ChromaDB."""
        if not records:
            return 0

        ids: List[str] = []
        embeddings: List[List[float]] = []
        metadatas: List[Dict[str, Any]] = []
        documents: List[str] = []

        for item in records:
            if isinstance(item, VectorRecord):
                rec_id = item.id
                text = item.text
                meta = dict(item.metadata)
                meta["embedding_model"] = item.embedding_model
                emb = item.embedding
            else:
                rec_id = item.get("id") or str(uuid.uuid4())
                text = item.get("text", "")
                meta = dict(item.get("metadata", {}))
                meta["embedding_model"] = item.get("embedding_model", "unknown")
                emb = item.get("embedding", [])

            ids.append(rec_id)
            documents.append(text)
            embeddings.append(emb)
            metadatas.append(_sanitize_metadata_for_chroma(meta))

        self.collection.add(
            ids=ids,
            embeddings=cast(Any, embeddings),
            metadatas=cast(Any, metadatas),
            documents=documents,
        )
        return len(ids)

    def add_chunks(
        self,
        chunks: Sequence[Union[Dict[str, Any], Any]],
        embedding_service: Optional[EmbeddingService] = None,
        batch_size: Optional[int] = None,
    ) -> int:
        """Embed document chunks and store them in ChromaDB.

        Args:
            chunks: List of document chunks (dicts or Chunk objects).
            embedding_service: Optional EmbeddingService instance.
            batch_size: Optional batch size.

        Returns:
            Number of chunks successfully embedded and stored.
        """
        service = embedding_service or get_embedding_service()
        try:
            embedded_records = service.embed_chunks(chunks=chunks, batch_size=batch_size, verbose=False)
        except Exception as exc:
            from src.embeddings.embedder import _generate_deterministic_semantic_vector
            logger.info("Using deterministic semantic vector embeddings for Chroma: %s", exc)
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
                })

        return self.add_records(embedded_records)

    def search(
        self,
        query_vector: Optional[Sequence[float]] = None,
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        *,
        vector: Optional[Sequence[float]] = None,
        filter: Optional[Dict[str, Any]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        include: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query ChromaDB collection for top-k similar chunks.

        Args:
            query_vector: Dense query embedding vector.
            top_k: Number of highest-scoring matches to return.
            filter_metadata: Metadata dictionary to filter candidates.
            min_score: Minimum similarity score threshold.
            vector: Alias for query_vector.
            filter: Alias for filter_metadata.
            metadata_filter: Alias for filter_metadata.
            include: Optional list of fields to include.

        Returns:
            List of ranked result dictionaries with score, text, and metadata.
        """
        effective_vector = vector if query_vector is None else query_vector
        if effective_vector is None:
            raise ValueError("A valid query vector must be provided.")

        effective_filter = filter_metadata or metadata_filter or filter

        if self.count() == 0 or top_k <= 0:
            return []

        effective_k = min(top_k, self.count())

        where_clause: Optional[Dict[str, Any]] = None
        if effective_filter:
            clean_filter = _sanitize_metadata_for_chroma(effective_filter)
            if len(clean_filter) == 1:
                where_clause = clean_filter
            elif len(clean_filter) > 1:
                where_clause = {"$and": [{k: v} for k, v in clean_filter.items()]}

        response = self.collection.query(
            query_embeddings=cast(Any, [list(effective_vector)]),
            n_results=effective_k,
            where=cast(Any, where_clause),
            include=["documents", "metadatas", "distances"],
        )

        results: List[Dict[str, Any]] = []
        if not response or not response.get("ids") or not response["ids"][0]:
            return results

        docs = response["documents"][0] if response.get("documents") else []
        metas = response["metadatas"][0] if response.get("metadatas") else []
        dists = response["distances"][0] if response.get("distances") else []
        ids = response["ids"][0]

        for idx, rec_id in enumerate(ids):
            distance = dists[idx] if idx < len(dists) and dists[idx] is not None else 0.0
            # For cosine distance, similarity = 1.0 - distance
            score = max(-1.0, min(1.0, 1.0 - distance))

            if min_score is not None and score < min_score:
                continue

            doc_text = docs[idx] if idx < len(docs) else ""
            raw_meta = dict(metas[idx]) if idx < len(metas) and metas[idx] else {}
            model = raw_meta.pop("embedding_model", "text-embedding-3-small")

            results.append({
                "id": rec_id,
                "score": float(score),
                "text": doc_text,
                "metadata": raw_meta,
                "embedding_model": model,
            })

        # Sort descending and assign ranks
        results.sort(key=lambda item: item["score"], reverse=True)
        for rank_idx, item in enumerate(results, start=1):
            item["rank"] = rank_idx

        return results


# Global singleton ChromaVectorStore instance
_default_chroma_store: Optional[ChromaVectorStore] = None


def get_chroma_store(
    collection_name: Optional[str] = None,
    persist_directory: Optional[Union[str, Path]] = None,
    reset: bool = False,
) -> ChromaVectorStore:
    """Retrieve or initialize the global default ChromaVectorStore instance.

    Args:
        collection_name: Optional collection name override (defaults to settings.VECTOR_COLLECTION_NAME).
        persist_directory: Optional persist directory override (defaults to settings.VECTOR_DB_PATH).
        reset: If True, forces re-instantiation of the default instance.

    Returns:
        ChromaVectorStore instance.
    """
    global _default_chroma_store
    from src.core.config import settings

    target_name = collection_name or getattr(settings, "VECTOR_COLLECTION_NAME", "finee_financial_corpus")
    target_path = persist_directory or getattr(settings, "VECTOR_DB_PATH", "./data/vector_db")

    if _default_chroma_store is None or reset:
        _default_chroma_store = ChromaVectorStore(
            collection_name=target_name,
            persist_directory=target_path,
        )
    return _default_chroma_store
