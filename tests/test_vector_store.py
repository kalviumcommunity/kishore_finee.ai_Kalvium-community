"""Unit test suite for Vector Database Setup and Insert/Readback Verification."""

import pytest
import numpy as np

from src.vector_store.service import (
    DimensionMismatchError,
    InvalidRecordError,
    SchemaMismatchError,
    VectorRecord,
    VectorStoreError,
    VectorStoreService,
    generate_stable_id,
)


import uuid


@pytest.fixture
def in_memory_vector_store() -> VectorStoreService:
    """Fixture providing a clean in-memory VectorStoreService instance for isolated testing."""
    unique_col_name = f"test_rag_chunks_{uuid.uuid4().hex[:8]}"
    return VectorStoreService(
        collection_name=unique_col_name,
        dimension=1536,
        distance_metric="cosine",
        in_memory=True,
    )



class TestCollectionCreationAndConfig:
    """Test suite for vector collection initialization and distance metrics."""

    def test_collection_created_with_cosine_metric(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify collection is created with the expected distance metric and dimension metadata."""
        col = in_memory_vector_store.get_or_create_collection()
        assert col is not None
        assert col.name == in_memory_vector_store.collection_name
        assert col.metadata.get("hnsw:space") == "cosine"
        assert col.metadata.get("dimension") == 1536


    def test_schema_mismatch_fails_on_incompatible_metric(self) -> None:
        """Verify connecting with an incompatible distance metric on existing collection raises error."""
        # Create collection with 'cosine'
        store_cosine = VectorStoreService(
            collection_name="shared_collection",
            dimension=1536,
            distance_metric="cosine",
            in_memory=True,
        )
        col = store_cosine.get_or_create_collection()
        client = store_cosine.connect()

        # Connect using another service pointing to same client but expecting 'l2'
        store_l2 = VectorStoreService(
            collection_name="shared_collection",
            dimension=1536,
            distance_metric="l2",
            client=client,
        )
        with pytest.raises(SchemaMismatchError, match="exists with metric 'cosine'"):
            store_l2.get_or_create_collection()


class TestDimensionAndVectorValidation:
    """Test suite for vector validation and dimension enforcement."""

    def test_valid_vector_accepted(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify valid vector of correct dimension is accepted."""
        vec = [0.1] * 1536
        validated = in_memory_vector_store.validate_vector(vec, record_id="test_rec")
        assert len(validated) == 1536
        assert isinstance(validated, list)

    def test_incorrect_dimension_rejected(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify vector with incorrect dimension raises DimensionMismatchError."""
        short_vec = [0.1] * 768
        with pytest.raises(DimensionMismatchError, match="expected 1536, got 768"):
            in_memory_vector_store.validate_vector(short_vec, record_id="short_rec")

    def test_empty_vector_rejected(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify empty vector raises InvalidRecordError."""
        with pytest.raises(InvalidRecordError, match="cannot be empty"):
            in_memory_vector_store.validate_vector([], record_id="empty_rec")

    def test_non_numeric_vector_rejected(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify non-numeric elements raise InvalidRecordError."""
        bad_vec = ["invalid"] * 1536
        with pytest.raises(InvalidRecordError, match="contains non-numeric values"):
            in_memory_vector_store.validate_vector(bad_vec, record_id="bad_rec")

    def test_nan_or_inf_vector_rejected(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify NaN or Inf vector elements raise InvalidRecordError."""
        nan_vec = [float("nan")] * 1536
        with pytest.raises(InvalidRecordError, match="contains NaN or infinite"):
            in_memory_vector_store.validate_vector(nan_vec, record_id="nan_rec")


class TestStableIdGeneration:
    """Test suite for deterministic stable chunk IDs."""

    def test_stable_id_from_document_id_and_chunk_index(self) -> None:
        """Verify ID is formatted as document_id:chunk_index."""
        rec = {
            "metadata": {
                "document_id": "client_agreement.pdf",
                "chunk_index": 4,
            }
        }
        assert generate_stable_id(rec) == "client_agreement.pdf:4"

    def test_stable_id_fallback_to_source(self) -> None:
        """Verify ID falls back to source filename if document_id is missing."""
        rec = {
            "metadata": {
                "source": "fee_schedule.pdf",
                "chunk_index": 2,
            }
        }
        assert generate_stable_id(rec) == "fee_schedule.pdf:2"

    def test_explicit_id_preserved(self) -> None:
        """Verify explicit ID is preserved if provided."""
        rec = {"id": "custom-uuid-1234"}
        assert generate_stable_id(rec) == "custom-uuid-1234"


class TestUpsertAndReadback:
    """Test suite for inserting records and reading them back with exact fidelity."""

    def test_upsert_and_readback_preserves_all_fields(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify upserting and reading back preserves ID, text, metadata, and embedding vector."""
        vec = [float(i % 50) / 50.0 for i in range(1536)]
        test_record = {
            "id": "compliance-doc.pdf:0",
            "text": "Advisory fees must be disclosed quarterly under compliance rules.",
            "metadata": {
                "source": "compliance-doc.pdf",
                "document_id": "compliance-doc.pdf",
                "document_version": "1.0",
                "chunk_index": 0,
                "page": 1,
                "section": "Fee Disclosures",
                "approval_status": "approved",
            },
            "embedding": vec,
            "embedding_model": "text-embedding-3-small",
        }

        inserted_id = in_memory_vector_store.upsert_record(test_record)
        assert inserted_id == "compliance-doc.pdf:0"

        # Read back by ID
        readback = in_memory_vector_store.get_record_by_id(inserted_id)
        assert readback is not None
        assert readback["id"] == "compliance-doc.pdf:0"
        assert readback["text"] == test_record["text"]
        assert readback["metadata"]["source"] == "compliance-doc.pdf"
        assert readback["metadata"]["section"] == "Fee Disclosures"
        assert readback["metadata"]["embedding_model"] == "text-embedding-3-small"
        assert readback["embedding_dimension"] == 1536
        assert pytest.approx(readback["vector"][:5], 1e-5) == vec[:5]

    def test_upsert_idempotency_updates_without_duplicates(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify re-running upsert with the same ID updates the record without creating duplicate entries."""
        vec = [0.1] * 1536
        rec_v1 = {
            "id": "doc1.pdf:0",
            "text": "Initial text version",
            "metadata": {"source": "doc1.pdf", "chunk_index": 0, "version": 1},
            "embedding": vec,
        }
        in_memory_vector_store.upsert_record(rec_v1)
        assert in_memory_vector_store.count() == 1

        # Re-upsert with updated text under same ID
        rec_v2 = {
            "id": "doc1.pdf:0",
            "text": "Updated text version",
            "metadata": {"source": "doc1.pdf", "chunk_index": 0, "version": 2},
            "embedding": vec,
        }
        in_memory_vector_store.upsert_record(rec_v2)

        # Count should remain 1, but text and metadata should reflect version 2
        assert in_memory_vector_store.count() == 1
        readback = in_memory_vector_store.get_record_by_id("doc1.pdf:0")
        assert readback is not None
        assert readback["text"] == "Updated text version"
        assert readback["metadata"]["version"] == 2

    def test_end_to_end_verification_routine(self, in_memory_vector_store: VectorStoreService) -> None:
        """Verify verify_insert_and_readback executes successfully and produces a passing report."""
        result = in_memory_vector_store.verify_insert_and_readback()
        assert result["readback_successful"] is True
        assert result["text_preserved"] is True
        assert result["metadata_preserved"] is True
        assert result["dimension_valid"] is True
        assert result["vector_length"] == 1536

        report = in_memory_vector_store.generate_verification_report(result)
        assert "Vector Store Verification" in report
        assert "Collection: test_rag_chunks" in report
        assert "Dimension: 1536" in report
        assert "Metric: cosine" in report
        assert "Text preserved: PASS" in report
        assert "Metadata preserved: PASS" in report
        assert "Readback successful: PASS" in report
