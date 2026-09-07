"""Unit and integration test suite for Similarity Search and Top-K Retrieval."""

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch
import pytest

from src.embeddings.embedding_service import (
    EmbeddingService,
    get_embedding_service,
)
from src.retrieval.retriever import (
    RetrievalResult,
    compare_k_retrieval,
    retrieve,
)
from src.retrieval.vector_store import (
    InMemoryVectorStore,
    VectorRecord,
)
from scripts.demonstrate_retrieval import (
    CORPUS_CHUNKS,
    OUTPUT_FILE_DEMO,
    OUTPUT_FILE_PRIMARY,
    build_demo_vector_store,
    run_retrieval_demonstration,
)


@pytest.fixture
def sample_vector_records() -> List[VectorRecord]:
    """Sample pre-embedded vector records for testing similarity search."""
    return [
        VectorRecord(
            id="vec_001",
            text="How to reset account password using self-service portal.",
            metadata={"source": "auth-guide.md", "chunk_index": 0, "approval_status": "approved"},
            embedding=[0.9, 0.8, 0.1, 0.0],
            embedding_model="text-embedding-3-small",
        ),
        VectorRecord(
            id="vec_002",
            text="Two-factor authentication and login credentials recovery.",
            metadata={"source": "auth-guide.md", "chunk_index": 1, "approval_status": "approved"},
            embedding=[0.8, 0.7, 0.2, 0.1],
            embedding_model="text-embedding-3-small",
        ),
        VectorRecord(
            id="vec_003",
            text="Mutual fund Total Expense Ratio (TER) and management fees.",
            metadata={"source": "mf-handbook.pdf", "chunk_index": 0, "approval_status": "approved"},
            embedding=[0.1, 0.2, 0.9, 0.8],
            embedding_model="text-embedding-3-small",
        ),
        VectorRecord(
            id="vec_004",
            text="Draft internal policy on employee cafeteria lunch schedule.",
            metadata={"source": "cafeteria.txt", "chunk_index": 0, "approval_status": "draft"},
            embedding=[0.0, 0.1, 0.1, 0.9],
            embedding_model="text-embedding-3-small",
        ),
    ]


@pytest.fixture
def sample_vector_store(sample_vector_records: List[VectorRecord]) -> InMemoryVectorStore:
    """Pre-populated in-memory vector store."""
    store = InMemoryVectorStore(name="test_collection")
    store.add(sample_vector_records)
    return store


class TestVectorRecordAndStore:
    """Tests for VectorRecord model and InMemoryVectorStore indexing."""

    def test_vector_record_creation_and_dict(self) -> None:
        """1. VectorRecord generates default ID and converts cleanly to dict."""
        rec = VectorRecord(
            text="Sample chunk text",
            metadata={"source": "doc.md", "chunk_index": 0},
            embedding=[0.1, 0.2, 0.3],
            embedding_model="text-embedding-3-small",
        )
        assert rec.id is not None
        assert rec.text == "Sample chunk text"
        assert rec.metadata["source"] == "doc.md"
        assert len(rec.embedding) == 3

        d = rec.to_dict()
        assert d["id"] == rec.id
        assert d["text"] == rec.text
        assert d["metadata"] == rec.metadata
        assert d["embedding_model"] == "text-embedding-3-small"
        assert "created_at" in d

    def test_vector_store_add_and_count(self, sample_vector_store: InMemoryVectorStore) -> None:
        """2. Vector store correctly counts and stores records."""
        assert sample_vector_store.count() == 4

        # Add dictionary record
        added = sample_vector_store.add([
            {
                "text": "Additional chunk",
                "metadata": {"source": "new.md", "chunk_index": 0},
                "embedding": [0.5, 0.5, 0.5, 0.5],
                "embedding_model": "text-embedding-3-small",
            }
        ])
        assert added == 1
        assert sample_vector_store.count() == 5

    def test_vector_store_clear(self, sample_vector_store: InMemoryVectorStore) -> None:
        """3. Vector store clear removes all indexed items."""
        assert sample_vector_store.count() > 0
        sample_vector_store.clear()
        assert sample_vector_store.count() == 0

    def test_vector_store_serialization(self, sample_vector_store: InMemoryVectorStore) -> None:
        """4. Vector store serializes to and deserializes from dictionary."""
        serialized = sample_vector_store.to_dict()
        assert serialized["name"] == "test_collection"
        assert serialized["count"] == 4
        assert len(serialized["records"]) == 4

        restored_store = InMemoryVectorStore.from_dict(serialized)
        assert restored_store.count() == 4
        assert restored_store.name == "test_collection"


class TestTopKSimilaritySearch:
    """Tests for similarity search, ranking, and metadata filtering."""

    def test_search_ranks_by_similarity_descending(
        self, sample_vector_store: InMemoryVectorStore
    ) -> None:
        """5. Search results are returned sorted in descending order of similarity score."""
        query_vector = [0.95, 0.85, 0.15, 0.0]
        results = sample_vector_store.search(query_vector=query_vector, top_k=3)

        assert len(results) == 3
        # Check descending scores
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Top match should be the password reset record (vec_001)
        assert results[0]["id"] == "vec_001"
        assert results[0]["rank"] == 1
        assert results[0]["score"] > 0.9

    def test_top_k_limiting(self, sample_vector_store: InMemoryVectorStore) -> None:
        """6. top_k parameter strictly caps returned results."""
        query_vector = [0.9, 0.8, 0.1, 0.0]

        res_k1 = sample_vector_store.search(query_vector=query_vector, top_k=1)
        assert len(res_k1) == 1
        assert res_k1[0]["rank"] == 1

        res_k2 = sample_vector_store.search(query_vector=query_vector, top_k=2)
        assert len(res_k2) == 2
        assert [r["rank"] for r in res_k2] == [1, 2]

        res_k10 = sample_vector_store.search(query_vector=query_vector, top_k=10)
        assert len(res_k10) == 4  # total available

    def test_search_with_metadata_filtering(
        self, sample_vector_store: InMemoryVectorStore
    ) -> None:
        """7. Metadata filtering restricts candidates based on metadata keys."""
        query_vector = [0.0, 0.1, 0.1, 0.9]  # close to cafeteria chunk

        # Without filter, cafeteria chunk is returned
        all_res = sample_vector_store.search(query_vector=query_vector, top_k=1)
        assert all_res[0]["id"] == "vec_004"

        # With approval_status="approved" filter, draft cafeteria chunk is excluded
        approved_res = sample_vector_store.search(
            query_vector=query_vector,
            top_k=4,
            filter_metadata={"approval_status": "approved"},
        )
        assert len(approved_res) == 3
        assert all(r["metadata"]["approval_status"] == "approved" for r in approved_res)
        assert "vec_004" not in [r["id"] for r in approved_res]

    def test_search_with_min_score_threshold(
        self, sample_vector_store: InMemoryVectorStore
    ) -> None:
        """8. min_score excludes chunks with similarity below the threshold."""
        query_vector = [0.9, 0.8, 0.1, 0.0]
        results = sample_vector_store.search(query_vector=query_vector, top_k=4, min_score=0.8)
        assert all(r["score"] >= 0.8 for r in results)


class TestRetrievalPipelineAndTasks:
    """Tests for Task 1-5 compliance in retrieval function."""

    def test_task1_same_model_query_embedding(self) -> None:
        """Task 1: Query is embedded using the exact same model as document chunks."""
        mock_service = MagicMock(spec=EmbeddingService)
        mock_service.model = "text-embedding-3-small"
        mock_service.embed_query.return_value = [0.9, 0.8, 0.1, 0.0]

        store = InMemoryVectorStore()
        store.add([
            VectorRecord(
                text="Password reset chunk",
                metadata={"source": "auth.md", "chunk_index": 0},
                embedding=[0.9, 0.8, 0.1, 0.0],
                embedding_model="text-embedding-3-small",
            )
        ])

        results = retrieve(
            query="How to reset password?",
            k=1,
            collection=store,
            embedding_service=mock_service,
        )

        # Verified embed_query was called with the user query string
        mock_service.embed_query.assert_called_once_with("How to reset password?")
        assert len(results) == 1
        assert results[0]["embedding_model"] == "text-embedding-3-small"

    def test_task2_and_task3_scores_and_metadata(
        self, sample_vector_store: InMemoryVectorStore
    ) -> None:
        """Task 2 & 3: Retrieval returns top-k chunks with score, text, and source metadata."""
        mock_service = MagicMock(spec=EmbeddingService)
        mock_service.model = "text-embedding-3-small"
        mock_service.embed_query.return_value = [0.9, 0.8, 0.1, 0.0]

        results = retrieve(
            query="Reset password",
            k=3,
            collection=sample_vector_store,
            embedding_service=mock_service,
        )

        assert len(results) == 3
        for rank, res in enumerate(results, start=1):
            assert res["rank"] == rank
            assert "score" in res
            assert isinstance(res["score"], float)
            assert "text" in res and len(res["text"]) > 0
            assert "metadata" in res and isinstance(res["metadata"], dict)
            assert "source" in res["metadata"]
            assert "chunk_index" in res["metadata"]
            assert "embedding_model" in res

    def test_task4_demonstrate_changing_k(
        self, sample_vector_store: InMemoryVectorStore
    ) -> None:
        """Task 4: Demonstrate retrieval across multiple k values (k=1, 3, 5)."""
        mock_service = MagicMock(spec=EmbeddingService)
        mock_service.model = "text-embedding-3-small"
        mock_service.embed_query.return_value = [0.9, 0.8, 0.1, 0.0]

        comparison = compare_k_retrieval(
            query="Reset password",
            k_values=[1, 2, 4],
            collection=sample_vector_store,
            embedding_service=mock_service,
        )

        assert comparison["query"] == "Reset password"
        assert "k_1" in comparison["results_by_k"]
        assert "k_2" in comparison["results_by_k"]
        assert "k_4" in comparison["results_by_k"]

        assert len(comparison["results_by_k"]["k_1"]) == 1
        assert len(comparison["results_by_k"]["k_2"]) == 2
        assert len(comparison["results_by_k"]["k_4"]) == 4

        summary = comparison["comparison_summary"]
        assert len(summary) == 3
        assert summary[0]["k"] == 1
        assert summary[0]["total_chunks_returned"] == 1

    def test_input_validations(self, sample_vector_store: InMemoryVectorStore) -> None:
        """Verify error handling on invalid query, k, or collection parameters."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            retrieve(query="", k=3, collection=sample_vector_store)

        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            retrieve(query="   ", k=3, collection=sample_vector_store)

        with pytest.raises(ValueError, match="A valid VectorStore collection must be provided"):
            retrieve(query="valid query", k=3, collection=None)

        # k <= 0 returns empty list
        empty_res = retrieve(query="valid query", k=0, collection=sample_vector_store)
        assert empty_res == []

        negative_res = retrieve(query="valid query", k=-2, collection=sample_vector_store)
        assert negative_res == []


class TestDemonstrationScriptExecution:
    """Tests executing the demonstration script and verifying output artifacts."""

    def test_run_retrieval_demonstration_executes_and_saves_files(self) -> None:
        """Task 5: Demonstration runs successfully and writes evaluation JSON files."""
        result = run_retrieval_demonstration()

        assert result["status"] == "success"
        assert "sample_retrieval_k3" in result
        assert len(result["sample_retrieval_k3"]) == 3
        assert "k_tradeoff_demonstration" in result
        assert "all_queries_evaluated" in result
        assert len(result["all_queries_evaluated"]) >= 4

        assert OUTPUT_FILE_PRIMARY.exists()
        assert OUTPUT_FILE_DEMO.exists()


class TestChromaVectorStoreIntegration:
    """Tests for ChromaDB vector store integration."""

    def test_chroma_store_add_and_search(self, sample_vector_records: List[VectorRecord]) -> None:
        """Verify ChromaVectorStore indexing and cosine search."""
        from src.retrieval.chroma_store import ChromaVectorStore

        chroma_store = ChromaVectorStore(collection_name="test_chroma_unit")
        chroma_store.clear()

        added = chroma_store.add_records(sample_vector_records)
        assert added == 4
        assert chroma_store.count() == 4

        # Search top-2
        query_vector = [0.95, 0.85, 0.15, 0.0]
        results = chroma_store.search(query_vector=query_vector, top_k=2)

        assert len(results) == 2
        assert results[0]["id"] == "vec_001"
        assert results[0]["rank"] == 1
        assert results[0]["metadata"]["source"] == "auth-guide.md"

        # Metadata filtering in Chroma
        filtered = chroma_store.search(
            query_vector=query_vector,
            top_k=4,
            filter_metadata={"approval_status": "approved"},
        )
        assert len(filtered) == 3
        assert all(r["metadata"]["approval_status"] == "approved" for r in filtered)

        # End-to-end retrieve function with Chroma store
        mock_service = MagicMock(spec=EmbeddingService)
        mock_service.model = "text-embedding-3-small"
        mock_service.embed_query.return_value = query_vector

        retrieved_items = retrieve(
            query="Reset password",
            k=2,
            collection=chroma_store,  # type: ignore[arg-type]
            embedding_service=mock_service,
        )
        assert len(retrieved_items) == 2
        assert retrieved_items[0]["rank"] == 1
        assert "score" in retrieved_items[0]

