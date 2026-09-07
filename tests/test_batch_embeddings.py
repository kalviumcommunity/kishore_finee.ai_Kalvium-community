"""Unit test suite for Batch Embedding & Rate/Cost Management."""

from pathlib import Path
from typing import Any, Dict, List
import pytest

from src.embeddings.batch_embedder import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_PRICE_PER_1K_TOKENS,
    BatchEmbedder,
    BatchRunSummary,
    batches,
)
from src.embeddings.embedder import DEFAULT_VECTOR_DIMENSION, _generate_deterministic_semantic_vector
from scripts.demonstrate_batch_embeddings import (
    OUTPUT_FILE,
    get_sample_financial_chunks,
    run_batch_embedding_demonstration,
)


class TestBatchGenerator:
    """Test suite for the `batches` generator."""

    def test_batches_exact_division(self) -> None:
        """Verifies batching when total items is an exact multiple of batch size."""
        items = list(range(12))
        batch_list = list(batches(items, size=4))
        assert len(batch_list) == 3
        assert batch_list[0] == [0, 1, 2, 3]
        assert batch_list[1] == [4, 5, 6, 7]
        assert batch_list[2] == [8, 9, 10, 11]

    def test_batches_with_remainder(self) -> None:
        """Verifies batching when total items leaves a remainder."""
        items = list(range(10))
        batch_list = list(batches(items, size=3))
        assert len(batch_list) == 4
        assert batch_list[0] == [0, 1, 2]
        assert batch_list[1] == [3, 4, 5]
        assert batch_list[2] == [6, 7, 8]
        assert batch_list[3] == [9]

    def test_batches_single_batch(self) -> None:
        """Verifies batching when batch size is larger than sequence length."""
        items = [1, 2, 3]
        batch_list = list(batches(items, size=10))
        assert len(batch_list) == 1
        assert batch_list[0] == [1, 2, 3]

    def test_batches_empty_sequence(self) -> None:
        """Verifies batching on an empty sequence produces no batches."""
        batch_list = list(batches([], size=5))
        assert len(batch_list) == 0

    def test_batches_invalid_size(self) -> None:
        """Verifies that non-positive batch sizes raise ValueError."""
        with pytest.raises(ValueError, match="Batch size must be a positive integer"):
            list(batches([1, 2, 3], size=0))

        with pytest.raises(ValueError, match="Batch size must be a positive integer"):
            list(batches([1, 2, 3], size=-5))


class TestBatchEmbedder:
    """Test suite for BatchEmbedder pipeline, retry logic, cost tracking, and skip-on-rerun."""

    @pytest.fixture
    def sample_chunks(self) -> List[Dict[str, Any]]:
        return [
            {"id": "chunk_1", "text": "High yield savings accounts pay interest on balances."},
            {"id": "chunk_2", "text": "Roth IRAs provide tax-free growth and distributions."},
            {"id": "chunk_3", "text": "Diversification reduces portfolio unsystematic risk."},
            {"id": "chunk_4", "text": "Municipal bonds offer tax exempt income for taxpayers."},
            {"id": "chunk_5", "text": "Emergency funds protect against unforeseen liquidity shocks."},
        ]

    def test_initial_cold_start_embedding(self, sample_chunks: List[Dict[str, Any]]) -> None:
        """Verifies that an initial run with no cached embeddings embeds all chunks in batches."""
        embedder = BatchEmbedder(batch_size=2)
        store, summary = embedder.process_corpus(sample_chunks)

        assert summary.total_chunks == 5
        assert summary.skipped_existing == 0
        assert summary.embedded == 5
        assert summary.failed == 0
        assert summary.batches_processed == 3  # (2 + 2 + 1)
        assert summary.input_tokens > 0
        assert summary.estimated_cost_usd > 0.0
        assert len(store) == 5
        for chunk in sample_chunks:
            assert chunk["id"] in store
            assert len(store[chunk["id"]]) == DEFAULT_VECTOR_DIMENSION

    def test_skip_already_embedded_chunks_on_rerun(self, sample_chunks: List[Dict[str, Any]]) -> None:
        """Verifies that re-running over existing embeddings skips 100% of chunks with 0 cost."""
        embedder = BatchEmbedder(batch_size=2)
        initial_store, initial_summary = embedder.process_corpus(sample_chunks)

        # Re-run on the exact same corpus using the existing embeddings
        rerun_store, rerun_summary = embedder.process_corpus(
            sample_chunks,
            existing_embeddings=initial_store,
        )

        assert rerun_summary.total_chunks == 5
        assert rerun_summary.skipped_existing == 5
        assert rerun_summary.embedded == 0
        assert rerun_summary.failed == 0
        assert rerun_summary.batches_processed == 0
        assert rerun_summary.input_tokens == 0
        assert rerun_summary.estimated_cost_usd == 0.0
        assert len(rerun_store) == 5

    def test_incremental_embedding(self, sample_chunks: List[Dict[str, Any]]) -> None:
        """Verifies that adding new chunks to an existing store only embeds the new items."""
        embedder = BatchEmbedder(batch_size=2)
        initial_store, _ = embedder.process_corpus(sample_chunks[:3])
        assert len(initial_store) == 3

        # Run with all 5 chunks (3 existing + 2 new)
        updated_store, summary = embedder.process_corpus(
            sample_chunks,
            existing_embeddings=initial_store,
        )

        assert summary.total_chunks == 5
        assert summary.skipped_existing == 3
        assert summary.embedded == 2
        assert summary.failed == 0
        assert len(updated_store) == 5

    def test_retry_with_backoff_transient_error(self, sample_chunks: List[Dict[str, Any]]) -> None:
        """Verifies that transient errors trigger exponential backoff retry and succeed."""
        call_count = {"count": 0}

        def mock_flaky_embed(texts: List[str]) -> List[List[float]]:
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise ConnectionError("429 Rate Limit Exceeded")
            return [_generate_deterministic_semantic_vector(t) for t in texts]

        embedder = BatchEmbedder(
            batch_size=5,
            max_attempts=3,
            initial_wait=0.01,
            embed_fn=mock_flaky_embed,
        )

        store, summary = embedder.process_corpus(sample_chunks)

        assert summary.retry_count == 1
        assert summary.embedded == 5
        assert summary.failed == 0
        assert call_count["count"] == 2
        assert len(store) == 5

    def test_retry_exhaustion_failure_tracked_in_summary(self, sample_chunks: List[Dict[str, Any]]) -> None:
        """Verifies that permanent failures after max retries are recorded in summary."""
        def mock_failing_embed(texts: List[str]) -> List[List[float]]:
            raise TimeoutError("504 Gateway Timeout")

        embedder = BatchEmbedder(
            batch_size=3,
            max_attempts=2,
            initial_wait=0.01,
            embed_fn=mock_failing_embed,
        )

        store, summary = embedder.process_corpus(sample_chunks)

        assert summary.total_chunks == 5
        assert summary.embedded == 0
        assert summary.failed == 5
        assert len(summary.failed_chunk_ids) == 5
        assert len(summary.errors) > 0
        assert len(store) == 0

    def test_cost_calculation(self) -> None:
        """Verifies exact token cost calculation."""
        embedder = BatchEmbedder(price_per_1k_tokens=0.00002)
        cost_1k = embedder.calculate_cost(1000)
        assert pytest.approx(cost_1k, 1e-9) == 0.00002

        cost_50k = embedder.calculate_cost(50000)
        assert pytest.approx(cost_50k, 1e-9) == 0.00100

    def test_summary_to_dict(self) -> None:
        """Verifies dictionary conversion of BatchRunSummary."""
        summary = BatchRunSummary(
            total_chunks=10,
            skipped_existing=4,
            embedded=6,
            failed=0,
            input_tokens=150,
            estimated_cost_usd=0.000003,
            batches_processed=2,
            retry_count=1,
            failed_chunk_ids=[],
            errors=[],
        )
        d = summary.to_dict()
        assert d["total_chunks"] == 10
        assert d["skipped_existing"] == 4
        assert d["embedded"] == 6
        assert d["input_tokens"] == 150
        assert d["batches_processed"] == 2


class TestDemonstrationScript:
    """Test suite for the demonstration script execution and output artifact."""

    def test_demonstration_script_execution(self) -> None:
        """Verifies that the demonstration script executes successfully end-to-end."""
        payload = run_batch_embedding_demonstration()

        assert payload["status"] == "success"
        assert payload["pipeline"] == "BatchEmbedder"
        assert payload["initial_run"]["embedded"] == 12
        assert payload["initial_run"]["batches_processed"] == 3
        assert payload["initial_run"]["retry_count"] >= 1
        assert payload["rerun_identical"]["skipped_existing"] == 12
        assert payload["rerun_identical"]["embedded"] == 0
        assert payload["rerun_identical"]["estimated_cost_usd"] == 0.0
        assert payload["incremental_run"]["skipped_existing"] == 12
        assert payload["incremental_run"]["embedded"] == 2
        assert payload["verification"]["batching_functional"] is True
        assert payload["verification"]["retry_handled_successfully"] is True
        assert payload["verification"]["rerun_skipped_all_existing"] is True
        assert payload["verification"]["rerun_zero_cost"] is True
        assert OUTPUT_FILE.exists()
