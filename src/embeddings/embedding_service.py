"""Embedding generation service for finee.ai.

Generates OpenAI-compatible vector embeddings for document chunks and queries,
maintaining complete provenance with chunk text, metadata, and model attribution.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field

from src.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_BATCH_SIZE = 50


class EmbeddingError(Exception):
    """Base exception for embedding generation errors."""
    pass


class EmbeddingConfigError(EmbeddingError):
    """Raised when embedding configuration or API key is missing or invalid."""
    pass


class EmbeddingAPIError(EmbeddingError):
    """Raised when the embeddings API request fails."""
    pass


class EmbeddingBatchError(EmbeddingError):
    """Raised when a specific batch of embeddings fails to process."""
    pass


class EmbeddingValidationError(EmbeddingError):
    """Raised when embedding output fails dimension or structure validation."""
    pass


class EmbeddingRecord(BaseModel):
    """Data structure representing an embedded document chunk."""

    text: str
    metadata: Dict[str, Any]
    embedding: List[float]
    embedding_model: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert embedding record to standard dictionary representation."""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at,
        }


class EmbeddingService:
    """Service for generating OpenAI-compatible embeddings with batching and validation."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        batch_size: Optional[int] = None,
        dimensions: Optional[int] = None,
        max_retries: int = 3,
        client: Optional[Any] = None,
    ) -> None:
        """Initialize embedding service with model parameters and API client.

        Args:
            model: Embedding model name (defaults to settings.EMBEDDING_MODEL).
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY).
            base_url: Optional OpenAI base URL (defaults to settings.OPENAI_BASE_URL).
            batch_size: Number of chunks per API request (defaults to settings.EMBEDDING_BATCH_SIZE).
            dimensions: Optional dimension override for embedding model.
            max_retries: Maximum retry attempts for transient API failures.
            client: Optional pre-configured OpenAI client instance (e.g. for testing/mocking).
        """
        self.model = model or settings.EMBEDDING_MODEL or settings.EMBED_MODEL or DEFAULT_EMBEDDING_MODEL
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.base_url = base_url if base_url is not None else settings.OPENAI_BASE_URL
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE or DEFAULT_EMBEDDING_BATCH_SIZE
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSIONS
        self.max_retries = max_retries
        self._client = client

    def _get_client(self) -> Any:
        """Lazily initialize or return the OpenAI API client."""
        if self._client is not None:
            return self._client

        if not self.api_key or not str(self.api_key).strip():
            raise EmbeddingConfigError(
                "OPENAI_API_KEY is not configured. Please set OPENAI_API_KEY in your "
                "environment or pass api_key to EmbeddingService."
            )

        try:
            from openai import OpenAI

            client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.base_url and self.base_url.strip():
                client_kwargs["base_url"] = self.base_url.strip().rstrip("/")

            self._client = OpenAI(**client_kwargs)
            return self._client
        except Exception as e:
            raise EmbeddingConfigError(f"Failed to initialize OpenAI client: {e}") from e

    def _call_api_with_retry(self, texts: List[str], batch_idx: int = 0) -> List[List[float]]:
        """Call the embeddings API with exponential backoff for transient errors."""
        client = self._get_client()

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "input": texts,
        }
        if self.dimensions:
            kwargs["dimensions"] = self.dimensions

        for attempt in range(1, self.max_retries + 1):
            try:
                response = client.embeddings.create(**kwargs)
                # Sort by index to maintain exact chunk-to-vector ordering
                sorted_data = sorted(response.data, key=lambda item: item.index)
                vectors = [item.embedding for item in sorted_data]

                if len(vectors) != len(texts):
                    raise EmbeddingValidationError(
                        f"API returned {len(vectors)} vectors for {len(texts)} input texts in batch {batch_idx}."
                    )

                return vectors

            except Exception as exc:
                exc_name = exc.__class__.__name__
                # Check for fatal non-retryable authentication / validation errors
                if "AuthenticationError" in exc_name or "PermissionDeniedError" in exc_name:
                    raise EmbeddingAPIError(
                        f"Authentication failed for batch {batch_idx}: {exc}"
                    ) from exc

                if "BadRequestError" in exc_name:
                    raise EmbeddingAPIError(
                        f"Bad request error for batch {batch_idx}: {exc}"
                    ) from exc

                if attempt == self.max_retries:
                    raise EmbeddingBatchError(
                        f"Embedding generation failed for batch {batch_idx} after {self.max_retries} attempts: {exc}"
                    ) from exc

                # Exponential backoff for rate limits or transient errors
                sleep_time = min(0.5 * (2 ** (attempt - 1)), 8.0)
                logger.warning(
                    f"Transient error in batch {batch_idx} (attempt {attempt}/{self.max_retries}): {exc}. "
                    f"Retrying in {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)

        raise EmbeddingBatchError(f"Embedding generation failed for batch {batch_idx}.")

    def embed_chunks(
        self,
        chunks: Sequence[Union[Dict[str, Any], Any]],
        batch_size: Optional[int] = None,
        skip_existing: bool = True,
        verbose: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate embedding vectors for a list of document chunks in batches.

        Args:
            chunks: List of chunk dictionaries or Chunk objects containing text and metadata.
            batch_size: Optional batch size override.
            skip_existing: If True, preserves chunks that already contain valid embeddings.
            verbose: If True, prints logging summary after embedding generation.

        Returns:
            List of embedding record dictionaries with text, metadata, embedding, model, and timestamp.
        """
        if not chunks:
            return []

        effective_batch_size = batch_size or self.batch_size
        if effective_batch_size <= 0:
            raise ValueError(f"batch_size must be a positive integer, got {effective_batch_size}")

        records: List[Dict[str, Any]] = []
        chunks_to_embed_indices: List[int] = []
        chunks_to_embed_texts: List[str] = []

        # 1. Normalize chunks and identify which need embedding
        for idx, item in enumerate(chunks):
            if isinstance(item, dict):
                text = item.get("text", "")
                metadata = item.get("metadata", {})
                existing_embedding = item.get("embedding")
                existing_model = item.get("embedding_model")
                existing_created_at = item.get("created_at")
            elif hasattr(item, "text") and hasattr(item, "metadata"):
                text = item.text
                metadata = item.metadata if isinstance(item.metadata, dict) else item.metadata.model_dump()
                existing_embedding = getattr(item, "embedding", None)
                existing_model = getattr(item, "embedding_model", None)
                existing_created_at = getattr(item, "created_at", None)
            else:
                raise ValueError(f"Invalid chunk format at index {idx}: must be dict or Chunk object.")

            if not isinstance(text, str):
                raise ValueError(f"Chunk text at index {idx} must be a string, got {type(text).__name__}.")

            # Re-run safety: reuse existing valid embedding if configured
            if skip_existing and existing_embedding and existing_model == self.model:
                records.append({
                    "text": text,
                    "metadata": metadata,
                    "embedding": existing_embedding,
                    "embedding_model": existing_model,
                    "created_at": existing_created_at or datetime.now(timezone.utc).isoformat(),
                })
            else:
                records.append({
                    "text": text,
                    "metadata": metadata,
                    "embedding": None,
                    "embedding_model": self.model,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                chunks_to_embed_indices.append(idx)
                chunks_to_embed_texts.append(text)

        # 2. Process chunks in batches
        if chunks_to_embed_texts:
            for start_idx in range(0, len(chunks_to_embed_texts), effective_batch_size):
                end_idx = start_idx + effective_batch_size
                batch_texts = chunks_to_embed_texts[start_idx:end_idx]
                batch_indices = chunks_to_embed_indices[start_idx:end_idx]
                batch_num = (start_idx // effective_batch_size) + 1

                vectors = self._call_api_with_retry(batch_texts, batch_idx=batch_num)

                for chunk_pos, vector in zip(batch_indices, vectors):
                    records[chunk_pos]["embedding"] = vector

        # 3. Validate generated embedding records
        self.validate_embeddings(records)

        # 4. Log development summary
        if verbose and records:
            sample_vec = records[0]["embedding"]
            sample_preview = [round(v, 4) for v in sample_vec[:5]]
            print(f"\nModel:\n{self.model}")
            print(f"\nRecords:\n{len(records)}")
            print(f"\nVector length:\n{len(sample_vec)}")
            print(f"\nSample values:\n{sample_preview}")

        return records

    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding vector for a single search query string.

        Guarantees that query embeddings use the identical model and embedding space
        as document chunk embeddings.

        Args:
            query: The query text to embed.

        Returns:
            List of floats representing the query vector.
        """
        if not isinstance(query, str):
            raise ValueError(f"Query must be a string, got {type(query).__name__}")

        if not query.strip():
            raise ValueError("Query text cannot be empty.")

        vectors = self._call_api_with_retry([query], batch_idx=0)
        return vectors[0]

    def embed_text(self, text: str) -> List[float]:
        """Convenience alias for embedding a single text string."""
        return self.embed_query(text)

    def validate_embeddings(
        self,
        records: Sequence[Dict[str, Any]],
        expected_dimension: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Validate embedding records for uniformity, numeric values, and metadata preservation.

        Args:
            records: List of embedding record dictionaries.
            expected_dimension: Optional expected vector dimension.

        Returns:
            Dictionary with validation summary statistics.

        Raises:
            EmbeddingValidationError: If any validation check fails.
        """
        if not records:
            return {"count": 0, "dimension": 0, "is_valid": True}

        first_vec = records[0].get("embedding")
        if first_vec is None or not isinstance(first_vec, list) or len(first_vec) == 0:
            raise EmbeddingValidationError("First chunk embedding is missing, empty, or not a list.")

        target_dim = expected_dimension or len(first_vec)

        for i, rec in enumerate(records):
            if "text" not in rec or rec["text"] is None:
                raise EmbeddingValidationError(f"Record {i} is missing original chunk text.")
            if "metadata" not in rec or not isinstance(rec["metadata"], dict):
                raise EmbeddingValidationError(f"Record {i} is missing chunk metadata dictionary.")
            if "embedding_model" not in rec or not rec["embedding_model"]:
                raise EmbeddingValidationError(f"Record {i} is missing embedding_model attribution.")

            vec = rec.get("embedding")
            if vec is None or not isinstance(vec, list) or len(vec) == 0:
                raise EmbeddingValidationError(f"Record {i} has empty or missing embedding vector.")

            if len(vec) != target_dim:
                raise EmbeddingValidationError(
                    f"Record {i} vector length ({len(vec)}) does not match expected dimension ({target_dim})."
                )

            if not all(isinstance(v, (int, float)) for v in vec):
                raise EmbeddingValidationError(f"Record {i} vector contains non-numeric values.")

        return {
            "count": len(records),
            "dimension": target_dim,
            "is_valid": True,
            "model": records[0].get("embedding_model"),
        }


# Global default service singleton
_default_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Retrieve or create the global default EmbeddingService instance."""
    global _default_service
    if _default_service is None:
        _default_service = EmbeddingService()
    return _default_service


def embed_chunks(
    chunks: Sequence[Union[Dict[str, Any], Any]],
    batch_size: Optional[int] = None,
    skip_existing: bool = True,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """Convenience function to generate embeddings for a list of document chunks."""
    return get_embedding_service().embed_chunks(
        chunks=chunks,
        batch_size=batch_size,
        skip_existing=skip_existing,
        verbose=verbose,
    )


def embed_query(query: str) -> List[float]:
    """Convenience function to generate an embedding for a search query using the configured model."""
    return get_embedding_service().embed_query(query)


def embed_text(text: str) -> List[float]:
    """Convenience function to generate an embedding for a text string."""
    return get_embedding_service().embed_text(text)



def main() -> None:
    """CLI smoke test and demonstration of chunk embedding generation."""
    print("=" * 60)
    print("FInee.ai - EMBEDDING GENERATION")
    print("=" * 60)

    sample_chunks = [
        {
            "text": "Marcus paid the advisory fee on 20 August.",
            "metadata": {
                "source": "client-payment-record.pdf",
                "document_id": "doc_001",
                "document_version": "1.0",
                "chunk_index": 0,
                "page": 2,
                "section": "Payment History",
                "approval_status": "approved",
            },
        },
        {
            "text": "The payment status was completed and verified.",
            "metadata": {
                "source": "client-payment-record.pdf",
                "document_id": "doc_001",
                "document_version": "1.0",
                "chunk_index": 1,
                "page": 2,
                "section": "Payment History",
                "approval_status": "approved",
            },
        },
    ]

    service = get_embedding_service()
    print(f"Configured Model : {service.model}")
    print(f"Batch Size       : {service.batch_size}")
    print(f"API Configured   : {bool(service.api_key)}")

    if service.api_key:
        try:
            records = service.embed_chunks(sample_chunks)
            print("\n" + "-" * 60)
            print("Generated Embedding Records:")
            print("-" * 60)
            for rec in records:
                print(f"Chunk {rec['metadata'].get('chunk_index')} | Source: {rec['metadata'].get('source')}")
                print(f"Text   : {rec['text']}")
                print(f"Model  : {rec['embedding_model']}")
                print(f"Vector : [{', '.join(f'{v:.4f}' for v in rec['embedding'][:5])}, ...]")
                print()
        except Exception as err:
            print(f"API Error during smoke test: {err}")
    else:
        print("\nNote: OPENAI_API_KEY is not configured in .env. Automated unit tests will mock API calls.")


if __name__ == "__main__":
    main()
