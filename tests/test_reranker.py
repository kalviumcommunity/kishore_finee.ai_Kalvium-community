"""Unit test suite for Candidate Re-ranking in finee.ai."""

import pytest
from unittest.mock import MagicMock, patch

from src.retrieval.reranker import (
    RerankConfigurationError,
    RerankError,
    format_rerank_comparison,
    parse_rerank_score,
    rerank,
    retrieve_and_rerank,
    score_relevance,
)
from src.retrieval.vector_store import InMemoryVectorStore


@pytest.fixture
def sample_candidates() -> list[dict]:
    """Fixture providing candidate chunk records with initial vector scores."""
    return [
        {
            "rank": 1,
            "score": 0.92,
            "text": "General commentary on investments and market updates.",
            "metadata": {"source": "general-guide.md", "chunk_index": 0},
            "id": "general-guide.md:0",
        },
        {
            "rank": 2,
            "score": 0.88,
            "text": "Specific invoice record: Marcus was billed an advisory fee of $1,250 on 20 August.",
            "metadata": {"source": "billing-invoice.pdf", "chunk_index": 1},
            "id": "billing-invoice.pdf:1",
        },
        {
            "rank": 3,
            "score": 0.85,
            "text": "Bond portfolio overview: Annual coupon distribution is paid semi-annually.",
            "metadata": {"source": "bond-overview.pdf", "chunk_index": 0},
            "id": "bond-overview.pdf:0",
        },
    ]


class TestScoreParsing:
    """Test suite for parsing model response text into clamped 0-10 numeric scores."""

    def test_parse_exact_numeric_scores(self) -> None:
        """Verify clean numeric string outputs parse into floats."""
        assert parse_rerank_score("8") == 8.0
        assert parse_rerank_score("9.5") == 9.5
        assert parse_rerank_score("0.0") == 0.0
        assert parse_rerank_score("10") == 10.0

    def test_parse_score_embedded_in_text(self) -> None:
        """Verify scores embedded in surrounding text are extracted."""
        assert parse_rerank_score("Relevance score: 8.5/10") == 8.5
        assert parse_rerank_score("The score is 7.2") == 7.2

    def test_parse_out_of_bounds_scores_clamped(self) -> None:
        """Verify scores outside 0-10 are clamped safely."""
        assert parse_rerank_score("15.5") == 10.0
        assert parse_rerank_score("-3.2") == 0.0

    def test_parse_malformed_output_uses_fallback(self) -> None:
        """Verify non-numeric text uses the documented fallback score."""
        assert parse_rerank_score("Irrelevant chunk without numbers", fallback_score=4.0) == 4.0
        assert parse_rerank_score("", fallback_score=5.0) == 5.0


class TestCandidateCountAndValidation:
    """Test suite for candidate_k and final_k constraints."""

    def test_invalid_candidate_k_rejected(self) -> None:
        """Verify candidate_k <= 0 raises RerankConfigurationError."""
        with pytest.raises(RerankConfigurationError, match="candidate_k must be a positive integer"):
            retrieve_and_rerank(query="test query", candidate_k=0, final_k=3)

        with pytest.raises(RerankConfigurationError, match="candidate_k must be a positive integer"):
            retrieve_and_rerank(query="test query", candidate_k=-5, final_k=3)

    def test_invalid_final_k_rejected(self) -> None:
        """Verify final_k <= 0 raises RerankConfigurationError."""
        with pytest.raises(RerankConfigurationError, match="final_k must be a positive integer"):
            retrieve_and_rerank(query="test query", candidate_k=10, final_k=0)

    def test_final_k_greater_than_candidate_k_rejected(self) -> None:
        """Verify final_k > candidate_k raises RerankConfigurationError."""
        with pytest.raises(RerankConfigurationError, match="cannot be greater than candidate_k"):
            retrieve_and_rerank(query="test query", candidate_k=3, final_k=10)

    def test_empty_query_rejected(self, sample_candidates: list[dict]) -> None:
        """Verify empty query string raises ValueError."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            rerank(query="", candidates=sample_candidates)

        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            rerank(query="   ", candidates=sample_candidates)

    def test_empty_candidates_returns_empty_list(self) -> None:
        """Verify empty candidate list returns an empty list cleanly."""
        assert rerank(query="valid query", candidates=[]) == []


class TestRankingOrderAndDataPreservation:
    """Test suite for sorting by rerank_score and preserving chunk fields."""

    def test_reranking_orders_by_rerank_score_descending(self, sample_candidates: list[dict]) -> None:
        """Verify candidates are sorted by rerank_score descending."""
        # Custom mock scorer providing specific scores:
        # Candidate 0 ("general"): 4.0
        # Candidate 1 ("billing"): 9.8 (Highest relevance)
        # Candidate 2 ("bond"): 2.0
        scores = {
            sample_candidates[0]["text"]: 4.0,
            sample_candidates[1]["text"]: 9.8,
            sample_candidates[2]["text"]: 2.0,
        }
        mock_scorer = lambda q, text: scores.get(text, 5.0)

        reranked = rerank(
            query="What is the billing fee for Marcus?",
            candidates=sample_candidates,
            final_k=3,
            scorer=mock_scorer,
        )

        assert len(reranked) == 3
        # Candidate 1 should now be Rank 1
        assert reranked[0]["id"] == "billing-invoice.pdf:1"
        assert reranked[0]["rerank_score"] == 9.8
        assert reranked[0]["rank"] == 1

        # Candidate 0 should now be Rank 2
        assert reranked[1]["id"] == "general-guide.md:0"
        assert reranked[1]["rerank_score"] == 4.0
        assert reranked[1]["rank"] == 2

        # Candidate 2 should now be Rank 3
        assert reranked[2]["id"] == "bond-overview.pdf:0"
        assert reranked[2]["rerank_score"] == 2.0
        assert reranked[2]["rank"] == 3

    def test_final_k_limits_output_count(self, sample_candidates: list[dict]) -> None:
        """Verify final_k returns exactly the requested number of top results."""
        reranked = rerank(
            query="What is the fee?",
            candidates=sample_candidates,
            final_k=2,
            scorer=lambda q, c: 8.0,
        )
        assert len(reranked) == 2

    def test_data_preservation_fidelity(self, sample_candidates: list[dict]) -> None:
        """Verify text, metadata, IDs, and initial vector scores are preserved without mutating input."""
        original_copy = [dict(c) for c in sample_candidates]

        reranked = rerank(
            query="What is the advisory fee for Marcus?",
            candidates=sample_candidates,
            final_k=3,
            scorer=lambda q, c: 9.0,
        )

        for original, res in zip(original_copy, sample_candidates):
            # Input list remains unmutated
            assert "rerank_score" not in original
            assert original == res

        # Output records preserve all original fields plus rerank_score
        billing_res = next(r for r in reranked if r["id"] == "billing-invoice.pdf:1")
        assert billing_res["text"] == sample_candidates[1]["text"]
        assert billing_res["metadata"] == sample_candidates[1]["metadata"]
        assert billing_res["score"] == sample_candidates[1]["score"]
        assert "rerank_score" in billing_res


class TestFormattingAndPipelineIntegration:
    """Test suite for comparison reporting and end-to-end retrieval integration."""

    def test_comparison_report_formatting(self, sample_candidates: list[dict]) -> None:
        """Verify format_rerank_comparison produces expected before/after sections."""
        reranked = rerank(query="What is the fee?", candidates=sample_candidates, final_k=2)
        pipeline_result = {
            "query": "What is the fee?",
            "candidate_k": 3,
            "final_k": 2,
            "initial_candidates": sample_candidates,
            "reranked_results": reranked,
            "metrics": {
                "candidate_count": 3,
                "final_count": 2,
                "retrieval_latency_seconds": 0.005,
                "rerank_latency_seconds": 0.012,
                "total_latency_seconds": 0.017,
                "rerank_calls": 3,
            },
        }

        report = format_rerank_comparison(pipeline_result)
        assert "Re-ranking Retrieval Comparison" in report
        assert "Before re-ranking (Initial Vector Retrieval):" in report
        assert "After re-ranking (Relevance-Scored Top-K):" in report
        assert "Performance & Latency Breakdown:" in report
        assert "Re-ranking calls: 3" in report

    def test_end_to_end_retrieve_and_rerank_with_vector_store(self) -> None:
        """Verify retrieve_and_rerank integrates with InMemoryVectorStore cleanly."""
        store = InMemoryVectorStore(name="test_store")
        store.add([
            {"id": "doc1:0", "text": "Advisory fee schedule 1.0%", "metadata": {"source": "fee.pdf"}, "embedding": [0.9, 0.1, 0.0], "embedding_model": "test"},
            {"id": "doc2:0", "text": "Bond distribution yield 4.0%", "metadata": {"source": "bond.pdf"}, "embedding": [0.1, 0.9, 0.0], "embedding_model": "test"},
            {"id": "doc3:0", "text": "Marcus paid fee invoice on 20 August", "metadata": {"source": "invoice.pdf"}, "embedding": [0.8, 0.2, 0.0], "embedding_model": "test"},
        ])

        with patch("src.retrieval.retriever._embed_query_safe", return_value=[0.85, 0.15, 0.0]):
            result = retrieve_and_rerank(
                query="What evidence shows the advisory fee charged to Marcus?",
                candidate_k=3,
                final_k=2,
                collection=store,
            )

        assert result["candidate_k"] == 3
        assert result["final_k"] == 2
        assert len(result["initial_candidates"]) == 3
        assert len(result["reranked_results"]) == 2
        assert result["metrics"]["rerank_calls"] == 3
        assert "total_latency_seconds" in result["metrics"]
