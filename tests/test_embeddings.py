"""Unit test suite for Embeddings Generation, Vector Representation, and LangChain integration."""

from pathlib import Path
from types import SimpleNamespace
from typing import List
from unittest.mock import MagicMock, patch
import pytest
import numpy as np
from langchain_core.embeddings import Embeddings

from src.core.config import Settings
from src.embeddings.embedder import (
    DEFAULT_VECTOR_DIMENSION,
    FIneeLangChainEmbeddings,
    cosine_similarity,
    embed,
    embed_text as langchain_embed_text,
    embed_texts as langchain_embed_texts,
    get_langchain_embeddings,
    verify_dimensions,
)
from src.embeddings.embedding_service import (
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingAPIError,
    EmbeddingBatchError,
    EmbeddingConfigError,
    EmbeddingError,
    EmbeddingRecord,
    EmbeddingService,
    EmbeddingValidationError,
    embed_chunks,
    embed_query,
    get_embedding_service,
)
from scripts.demonstrate_embeddings import run_embedding_demonstration, OUTPUT_FILE


def _create_mock_embedding_response(texts: List[str], dimension: int = 1536):
    """Helper to generate a mock OpenAI Embeddings API response object."""
    data = []
    for idx, text in enumerate(texts):
        # Create a distinct deterministic mock vector for each index
        vec = [float(idx + 1) * 0.01 + float(j) * 0.0001 for j in range(dimension)]
        data.append(SimpleNamespace(index=idx, embedding=vec))
    return SimpleNamespace(data=data)


class TestEmbeddingServiceGeneration:
    """Test suite for OpenAI-compatible EmbeddingService and batch embedding generation."""

    def test_embedding_service_initialization(self) -> None:
        """1. Verify embedding service initializes correctly with defaults and custom overrides."""
        service = EmbeddingService(api_key="test-key")
        assert service.model == DEFAULT_EMBEDDING_MODEL
        assert service.batch_size == DEFAULT_EMBEDDING_BATCH_SIZE
        assert service.api_key == "test-key"

        custom_service = EmbeddingService(
            model="text-embedding-3-large",
            api_key="custom-key",
            base_url="https://custom.api.com/v1",
            batch_size=25,
            dimensions=512,
        )
        assert custom_service.model == "text-embedding-3-large"
        assert custom_service.api_key == "custom-key"
        assert custom_service.base_url == "https://custom.api.com/v1"
        assert custom_service.batch_size == 25
        assert custom_service.dimensions == 512

    def test_api_configuration_loaded_from_settings(self) -> None:
        """2. Verify API configuration is loaded correctly from settings."""
        with patch("src.embeddings.embedding_service.settings") as mock_settings:
            mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"
            mock_settings.OPENAI_API_KEY = "env-openai-key"
            mock_settings.OPENAI_BASE_URL = "https://openai-compat.api/v1"
            mock_settings.EMBEDDING_BATCH_SIZE = 40
            mock_settings.EMBEDDING_DIMENSIONS = None

            service = EmbeddingService()
            assert service.model == "text-embedding-3-small"
            assert service.api_key == "env-openai-key"
            assert service.base_url == "https://openai-compat.api/v1"
            assert service.batch_size == 40

    def test_chunks_sent_as_batch(self) -> None:
        """3. Verify chunks are sent as a batch to the embeddings API."""
        mock_client = MagicMock()
        chunks = [
            {"text": "First chunk text", "metadata": {"source": "doc1.pdf", "chunk_index": 0}},
            {"text": "Second chunk text", "metadata": {"source": "doc1.pdf", "chunk_index": 1}},
            {"text": "Third chunk text", "metadata": {"source": "doc1.pdf", "chunk_index": 2}},
        ]
        mock_client.embeddings.create.return_value = _create_mock_embedding_response(
            [c["text"] for c in chunks]
        )

        service = EmbeddingService(api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, batch_size=10, verbose=False)

        assert mock_client.embeddings.create.call_count == 1
        call_kwargs = mock_client.embeddings.create.call_args.kwargs
        assert call_kwargs["input"] == ["First chunk text", "Second chunk text", "Third chunk text"]
        assert call_kwargs["model"] == service.model

    def test_number_of_returned_embeddings_matches_chunks(self) -> None:
        """4. Verify number of returned embeddings matches the number of input chunks."""
        mock_client = MagicMock()
        chunks = [
            {"text": f"Chunk text {i}", "metadata": {"source": "doc.pdf", "chunk_index": i}}
            for i in range(5)
        ]
        mock_client.embeddings.create.return_value = _create_mock_embedding_response(
            [c["text"] for c in chunks]
        )

        service = EmbeddingService(api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, verbose=False)

        assert len(records) == 5
        assert all(rec.get("embedding") is not None for rec in records)

    def test_embeddings_remain_associated_with_correct_chunk(self) -> None:
        """5. Verify embeddings remain associated with the exact matching chunk (index mapping)."""
        mock_client = MagicMock()
        chunks = [
            {"text": "Marcus paid the advisory fee on 20 August.", "metadata": {"source": "client.pdf", "chunk_index": 0}},
            {"text": "The payment status was completed.", "metadata": {"source": "client.pdf", "chunk_index": 1}},
        ]
        # Simulate API returning scrambled index order: [item 1, item 0]
        resp_data = [
            SimpleNamespace(index=1, embedding=[0.2, 0.2, 0.2]),
            SimpleNamespace(index=0, embedding=[0.1, 0.1, 0.1]),
        ]
        mock_client.embeddings.create.return_value = SimpleNamespace(data=resp_data)

        service = EmbeddingService(api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, verbose=False)

        # Chunk 0 must receive vector 0 ([0.1, 0.1, 0.1])
        assert records[0]["text"] == "Marcus paid the advisory fee on 20 August."
        assert records[0]["embedding"] == [0.1, 0.1, 0.1]

        # Chunk 1 must receive vector 1 ([0.2, 0.2, 0.2])
        assert records[1]["text"] == "The payment status was completed."
        assert records[1]["embedding"] == [0.2, 0.2, 0.2]

    def test_original_text_preserved(self) -> None:
        """6. Verify original chunk text is completely preserved in output records."""
        mock_client = MagicMock()
        original_text = "Important financial compliance text containing numbers: $1,250.00 and dates 2026-08-20."
        chunks = [{"text": original_text, "metadata": {"source": "report.pdf"}}]
        mock_client.embeddings.create.return_value = _create_mock_embedding_response([original_text])

        service = EmbeddingService(api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, verbose=False)

        assert records[0]["text"] == original_text

    def test_metadata_preserved(self) -> None:
        """7. Verify chunk metadata is completely preserved in output records."""
        mock_client = MagicMock()
        meta = {
            "source": "client-payment-record.pdf",
            "document_id": "doc_001",
            "document_version": "1.0",
            "chunk_index": 12,
            "page": 2,
            "section": "Payment History",
            "approval_status": "approved",
            "effective_date": "2026-08-20",
        }
        chunks = [{"text": "Marcus paid fee", "metadata": meta}]
        mock_client.embeddings.create.return_value = _create_mock_embedding_response(["Marcus paid fee"])

        service = EmbeddingService(api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, verbose=False)

        assert records[0]["metadata"] == meta

    def test_embedding_model_recorded(self) -> None:
        """8. Verify embedding model name and creation timestamp are recorded."""
        mock_client = MagicMock()
        chunks = [{"text": "Sample text", "metadata": {"source": "doc.pdf"}}]
        mock_client.embeddings.create.return_value = _create_mock_embedding_response(["Sample text"])

        service = EmbeddingService(model="text-embedding-3-small", api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, verbose=False)

        assert records[0]["embedding_model"] == "text-embedding-3-small"
        assert "created_at" in records[0]
        assert isinstance(records[0]["created_at"], str)

    def test_vector_length_validated(self) -> None:
        """9. Verify vector length and numeric values are validated."""
        service = EmbeddingService(api_key="test-key")

        # Valid record
        valid_records = [
            {
                "text": "sample",
                "metadata": {"source": "doc.pdf"},
                "embedding": [0.1, 0.2, 0.3],
                "embedding_model": "text-embedding-3-small",
            }
        ]
        result = service.validate_embeddings(valid_records)
        assert result["is_valid"] is True
        assert result["dimension"] == 3

        # Invalid: non-numeric values
        invalid_records = [
            {
                "text": "sample",
                "metadata": {"source": "doc.pdf"},
                "embedding": [0.1, "invalid", 0.3],
                "embedding_model": "text-embedding-3-small",
            }
        ]
        with pytest.raises(EmbeddingValidationError):
            service.validate_embeddings(invalid_records)

        # Invalid: mismatched dimension
        mismatched_records = [
            {"text": "s1", "metadata": {}, "embedding": [0.1, 0.2], "embedding_model": "m"},
            {"text": "s2", "metadata": {}, "embedding": [0.1, 0.2, 0.3], "embedding_model": "m"},
        ]
        with pytest.raises(EmbeddingValidationError):
            service.validate_embeddings(mismatched_records)

    def test_empty_input_handled(self) -> None:
        """10. Verify empty input returns empty list without calling API."""
        mock_client = MagicMock()
        service = EmbeddingService(api_key="test-key", client=mock_client)

        records = service.embed_chunks([], verbose=False)
        assert records == []
        assert mock_client.embeddings.create.call_count == 0

    def test_missing_api_key_handled(self) -> None:
        """11. Verify missing API key raises EmbeddingConfigError."""
        service = EmbeddingService(api_key=None)
        with patch.object(service, "api_key", None):
            with pytest.raises(EmbeddingConfigError, match="OPENAI_API_KEY is not configured"):
                service.embed_chunks([{"text": "Test", "metadata": {}}], verbose=False)

    def test_api_errors_handled_with_retry_and_fatal_failure(self) -> None:
        """12. Verify API errors are handled cleanly and retries trigger on transient errors."""
        mock_client = MagicMock()

        class RateLimitError(Exception):
            pass

        class AuthenticationError(Exception):
            pass

        # Transient error followed by success
        transient_err = RateLimitError("Rate limit exceeded")
        success_resp = _create_mock_embedding_response(["Test text"])
        mock_client.embeddings.create.side_effect = [transient_err, success_resp]

        service = EmbeddingService(api_key="test-key", client=mock_client, max_retries=2)
        with patch("time.sleep"):  # avoid test delays
            records = service.embed_chunks([{"text": "Test text", "metadata": {}}], verbose=False)

        assert len(records) == 1
        assert mock_client.embeddings.create.call_count == 2

        # Fatal non-retryable Authentication error
        auth_err = AuthenticationError("Invalid API Key")
        mock_client.embeddings.create.side_effect = auth_err

        with pytest.raises(EmbeddingAPIError, match="Authentication failed"):
            service.embed_chunks([{"text": "Test text", "metadata": {}}], verbose=False)


    def test_batch_processing_multiple_batches(self) -> None:
        """13. Verify batch processing works across multiple batches."""
        mock_client = MagicMock()
        # 12 chunks with batch_size=5 -> 3 batches (5, 5, 2)
        chunks = [
            {"text": f"Chunk {i}", "metadata": {"chunk_index": i}}
            for i in range(12)
        ]
        mock_client.embeddings.create.side_effect = [
            _create_mock_embedding_response([f"Chunk {i}" for i in range(5)]),
            _create_mock_embedding_response([f"Chunk {i}" for i in range(5, 10)]),
            _create_mock_embedding_response([f"Chunk {i}" for i in range(10, 12)]),
        ]

        service = EmbeddingService(api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, batch_size=5, verbose=False)

        assert len(records) == 12
        assert mock_client.embeddings.create.call_count == 3
        assert [r["text"] for r in records] == [f"Chunk {i}" for i in range(12)]

    def test_different_batch_sizes_handled(self) -> None:
        """14. Verify different configurable batch sizes are supported."""
        mock_client = MagicMock()
        chunks = [{"text": f"Chunk {i}", "metadata": {}} for i in range(6)]
        mock_client.embeddings.create.side_effect = [
            _create_mock_embedding_response([f"Chunk {i}" for i in range(2)]),
            _create_mock_embedding_response([f"Chunk {i}" for i in range(2, 4)]),
            _create_mock_embedding_response([f"Chunk {i}" for i in range(4, 6)]),
        ]

        service = EmbeddingService(api_key="test-key", batch_size=2, client=mock_client)
        records = service.embed_chunks(chunks, verbose=False)

        assert len(records) == 6
        assert mock_client.embeddings.create.call_count == 3

    def test_embed_query_uses_same_model(self) -> None:
        """15. Verify query embedding uses the identical model configuration."""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = _create_mock_embedding_response(["What is the fee?"])

        service = EmbeddingService(model="text-embedding-3-small", api_key="test-key", client=mock_client)
        query_vec = service.embed_query("What is the fee?")

        assert isinstance(query_vec, list)
        assert len(query_vec) == 1536
        call_kwargs = mock_client.embeddings.create.call_args.kwargs
        assert call_kwargs["model"] == "text-embedding-3-small"
        assert call_kwargs["input"] == ["What is the fee?"]

    def test_rerun_safety_skips_existing_embeddings(self) -> None:
        """16. Verify re-run safety skips chunks that already have valid embeddings for same model."""
        mock_client = MagicMock()
        existing_vector = [0.99] * 1536
        chunks = [
            {
                "text": "Already embedded chunk",
                "metadata": {"chunk_index": 0},
                "embedding": existing_vector,
                "embedding_model": "text-embedding-3-small",
            },
            {
                "text": "New chunk needing embedding",
                "metadata": {"chunk_index": 1},
            },
        ]
        mock_client.embeddings.create.return_value = _create_mock_embedding_response(
            ["New chunk needing embedding"]
        )

        service = EmbeddingService(model="text-embedding-3-small", api_key="test-key", client=mock_client)
        records = service.embed_chunks(chunks, skip_existing=True, verbose=False)

        assert len(records) == 2
        # Only the second chunk should have triggered an API call
        assert mock_client.embeddings.create.call_count == 1
        assert mock_client.embeddings.create.call_args.kwargs["input"] == ["New chunk needing embedding"]
        assert records[0]["embedding"] == existing_vector


class TestLangChainEmbeddings:
    """Test suite for LangChain embedding integration and vector representations."""

    def test_langchain_interface_compliance(self) -> None:
        """Verifies that our embeddings implementation complies with LangChain Embeddings interface."""
        embedder = get_langchain_embeddings()
        assert isinstance(embedder, Embeddings)
        assert hasattr(embedder, "embed_documents")
        assert hasattr(embedder, "embed_query")

    def test_embed_single_text_dimension(self) -> None:
        """Verifies that embedding a single query produces a vector of expected dimension."""
        text = "How do I reset my account password?"
        embedder = get_langchain_embeddings()
        vector = embedder.embed_query(text)

        assert isinstance(vector, list)
        assert len(vector) == DEFAULT_VECTOR_DIMENSION
        assert all(isinstance(v, float) for v in vector)

    def test_embed_batch_texts_uniform_dimensions(self) -> None:
        """Verifies that embed_documents returns vectors with uniform dimensionality."""
        texts = [
            "How do I reset my account password?",
            "Steps to recover access to my login",
            "The cafeteria menu has pasta today",
            "A short phrase",
            "A much longer financial disclaimer and policy explanation for compliance",
        ]
        embedder = get_langchain_embeddings()
        vectors = embedder.embed_documents(texts)

        assert len(vectors) == len(texts)
        verification = verify_dimensions(vectors)
        assert verification["is_uniform"] is True
        assert verification["dimension"] == DEFAULT_VECTOR_DIMENSION
        assert verification["count"] == len(texts)

    def test_embed_convenience_function(self) -> None:
        """Verifies that embed() handles both single strings and lists properly."""
        single_vec = embed("Single input string")
        assert isinstance(single_vec, list)
        assert len(single_vec) == DEFAULT_VECTOR_DIMENSION

        multi_vecs = embed(["First string", "Second string"])
        assert isinstance(multi_vecs, list)
        assert len(multi_vecs) == 2
        assert len(multi_vecs[0]) == DEFAULT_VECTOR_DIMENSION
        assert len(multi_vecs[1]) == DEFAULT_VECTOR_DIMENSION

    def test_cosine_similarity_properties(self) -> None:
        """Verifies mathematical properties of cosine similarity."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        v4 = [-1.0, 0.0, 0.0]

        # Self-similarity should be 1.0
        assert pytest.approx(cosine_similarity(v1, v2), 1e-6) == 1.0

        # Orthogonal vectors should have 0.0 similarity
        assert pytest.approx(cosine_similarity(v1, v3), 1e-6) == 0.0

        # Opposite vectors should have -1.0 similarity
        assert pytest.approx(cosine_similarity(v1, v4), 1e-6) == -1.0

        # Commutativity: sim(a, b) == sim(b, a)
        random_a = [0.5, 0.2, 0.8]
        random_b = [0.1, 0.9, 0.3]
        assert pytest.approx(cosine_similarity(random_a, random_b), 1e-6) == cosine_similarity(random_b, random_a)

    def test_cosine_similarity_validation_errors(self) -> None:
        """Verifies validation on dimension mismatch and empty vectors."""
        with pytest.raises(ValueError, match="Vector dimensions must match"):
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Cannot compute cosine similarity of empty vectors"):
            cosine_similarity([], [])

    def test_similar_vs_dissimilar_ranking(self) -> None:
        """Verifies that conceptually similar texts score higher than dissimilar texts."""
        embedder = get_langchain_embeddings()

        password_query = "How do I reset my account password?"
        login_recovery = "Steps to recover access to my login"
        cafeteria_menu = "The cafeteria menu has pasta today"

        vec_query = embedder.embed_query(password_query)
        vec_recovery = embedder.embed_query(login_recovery)
        vec_menu = embedder.embed_query(cafeteria_menu)

        sim_score = cosine_similarity(vec_query, vec_recovery)
        dissim_score = cosine_similarity(vec_query, vec_menu)

        assert sim_score > dissim_score
        assert (sim_score - dissim_score) > 0.15

    def test_financial_domain_ranking(self) -> None:
        """Verifies ranking on financial domain statements."""
        embedder = get_langchain_embeddings()

        finance_a = "What is the annual yield on a high-interest savings account?"
        finance_b = "How much interest does a high-yield savings deposit earn annually?"
        unrelated = "The football match was postponed due to heavy rain"

        vec_a = embedder.embed_query(finance_a)
        vec_b = embedder.embed_query(finance_b)
        vec_u = embedder.embed_query(unrelated)

        sim_score = cosine_similarity(vec_a, vec_b)
        dissim_score = cosine_similarity(vec_a, vec_u)

        assert sim_score > dissim_score
        assert (sim_score - dissim_score) > 0.20

    def test_demonstration_script_execution(self) -> None:
        """Verifies that the demonstration script runs end-to-end without errors."""
        result = run_embedding_demonstration()

        assert result["status"] == "success"
        assert result["framework"] == "LangChain"
        assert result["vector_dimension"] == DEFAULT_VECTOR_DIMENSION
        assert result["is_dimension_uniform"] is True
        assert len(result["samples"]) == 6
        assert len(result["comparisons"]) == 4
        assert result["ranking_validation"]["scenario_a_similar_higher"] is True
        assert result["ranking_validation"]["scenario_b_similar_higher"] is True
        assert OUTPUT_FILE.exists()
