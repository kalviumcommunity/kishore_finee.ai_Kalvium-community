"""Automated unit test suite for Embedding Retrieval Sanity Testing."""

from unittest.mock import MagicMock
import pytest
import numpy as np

from src.retrieval.sanity_checker import (
    DimensionMismatchError,
    InvalidVectorError,
    ModelMismatchError,
    SAMPLE_CHUNK_RECORDS,
    SAMPLE_SANITY_TEST_CASES,
    cosine_similarity,
    generate_sanity_report,
    rank_chunks,
    run_sanity_tests,
)


class TestCosineSimilarityValidation:
    """Test suite for cosine similarity calculations, properties, and input validation."""

    def test_identical_vectors_similarity_close_to_one(self) -> None:
        """Verify identical vectors have similarity of approximately 1.0."""
        vec = [0.2, 0.4, 0.6, 0.8]
        score = cosine_similarity(vec, vec)
        assert pytest.approx(score, 1e-6) == 1.0

    def test_orthogonal_vectors_similarity_close_to_zero(self) -> None:
        """Verify orthogonal vectors have similarity of approximately 0.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        score = cosine_similarity(vec_a, vec_b)
        assert pytest.approx(score, 1e-6) == 0.0

    def test_opposite_vectors_similarity_close_to_minus_one(self) -> None:
        """Verify opposite vectors have similarity of approximately -1.0."""
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [-1.0, -2.0, -3.0]
        score = cosine_similarity(vec_a, vec_b)
        assert pytest.approx(score, 1e-6) == -1.0

    def test_zero_vector_raises_invalid_vector_error(self) -> None:
        """Verify zero-norm vectors raise InvalidVectorError when allow_zero_norm is False."""
        zero_vec = [0.0, 0.0, 0.0]
        normal_vec = [1.0, 2.0, 3.0]
        with pytest.raises(InvalidVectorError, match="zero-norm vector"):
            cosine_similarity(zero_vec, normal_vec)

        # When allow_zero_norm=True, it returns 0.0 safely
        assert cosine_similarity(zero_vec, normal_vec, allow_zero_norm=True) == 0.0

    def test_empty_vectors_raise_invalid_vector_error(self) -> None:
        """Verify empty vectors raise InvalidVectorError."""
        with pytest.raises(InvalidVectorError, match="empty vectors"):
            cosine_similarity([], [])

    def test_dimension_mismatch_raises_error(self) -> None:
        """Verify mismatched vector dimensions raise DimensionMismatchError."""
        vec_a = [1.0, 2.0]
        vec_b = [1.0, 2.0, 3.0]
        with pytest.raises(DimensionMismatchError, match="Vector dimensions must match"):
            cosine_similarity(vec_a, vec_b)

    def test_nan_or_inf_raises_invalid_vector_error(self) -> None:
        """Verify vectors with NaN or Inf values raise InvalidVectorError."""
        vec_nan = [1.0, float("nan"), 3.0]
        vec_inf = [1.0, float("inf"), 3.0]
        vec_normal = [1.0, 2.0, 3.0]

        with pytest.raises(InvalidVectorError, match="NaN or infinite"):
            cosine_similarity(vec_nan, vec_normal)

        with pytest.raises(InvalidVectorError, match="NaN or infinite"):
            cosine_similarity(vec_inf, vec_normal)


class TestChunkRanking:
    """Test suite for chunk ranking and result sorting."""

    def test_correct_descending_ranking(self) -> None:
        """Verify chunks are sorted in strict descending order of similarity score."""
        query_vec = [1.0, 0.0, 0.0]
        chunks = [
            {"text": "Low similarity", "metadata": {"source": "low.pdf"}, "embedding": [0.1, 0.9, 0.0]},
            {"text": "High similarity", "metadata": {"source": "high.pdf"}, "embedding": [0.95, 0.1, 0.0]},
            {"text": "Medium similarity", "metadata": {"source": "med.pdf"}, "embedding": [0.5, 0.5, 0.0]},
        ]

        ranked = rank_chunks(query=query_vec, chunk_records=chunks, validate_model=False)

        assert len(ranked) == 3
        assert ranked[0]["metadata"]["source"] == "high.pdf"
        assert ranked[1]["metadata"]["source"] == "med.pdf"
        assert ranked[2]["metadata"]["source"] == "low.pdf"
        assert ranked[0]["score"] > ranked[1]["score"] > ranked[2]["score"]

    def test_original_metadata_and_text_preserved(self) -> None:
        """Verify original chunk text and metadata are preserved without mutating input."""
        query_vec = [1.0, 0.0, 0.0]
        meta = {
            "source": "fee-schedule.pdf",
            "document_id": "doc_001",
            "chunk_index": 5,
            "page": 3,
            "section": "Fee Terms",
        }
        original_chunk = {"text": "The fee is 1.0%.", "metadata": meta, "embedding": [1.0, 0.0, 0.0]}
        chunks_input = [original_chunk]

        ranked = rank_chunks(query=query_vec, chunk_records=chunks_input, validate_model=False)

        # Output record contains exact text and metadata + score
        assert ranked[0]["text"] == "The fee is 1.0%."
        assert ranked[0]["metadata"] == meta
        assert "score" in ranked[0]
        assert pytest.approx(ranked[0]["score"], 1e-6) == 1.0

        # Input list and dictionary remain unmutated (score not added to original chunk)
        assert "score" not in original_chunk

    def test_query_string_uses_embedding_service(self) -> None:
        """Verify query string triggers embedding service to generate query vector."""
        mock_service = MagicMock()
        mock_service.embed_query.return_value = [1.0, 0.0, 0.0]
        mock_service.model = "text-embedding-3-small"

        chunks = [
            {
                "text": "Advisory fee text",
                "metadata": {"source": "fee.pdf"},
                "embedding": [0.9, 0.1, 0.0],
                "embedding_model": "text-embedding-3-small",
            }
        ]

        ranked = rank_chunks(
            query="What is the fee?",
            chunk_records=chunks,
            embedding_service=mock_service,
            validate_model=True,
        )

        assert len(ranked) == 1
        assert mock_service.embed_query.called
        assert mock_service.embed_query.call_args[0][0] == "What is the fee?"


class TestModelAndDimensionCompatibility:
    """Test suite for model and dimension mismatch detection."""

    def test_model_mismatch_raises_error(self) -> None:
        """Verify comparing vectors from different models raises ModelMismatchError."""
        query_vec = [0.5, 0.5]
        chunks = [
            {
                "text": "Chunk from older ada model",
                "metadata": {"source": "doc.pdf"},
                "embedding": [0.5, 0.5],
                "embedding_model": "text-embedding-ada-002",
            }
        ]

        with pytest.raises(ModelMismatchError, match="Model mismatch"):
            rank_chunks(
                query=query_vec,
                chunk_records=chunks,
                validate_model=True,
                expected_model="text-embedding-3-small",
            )


    def test_dimension_mismatch_in_ranking_raises_error(self) -> None:
        """Verify vector dimension mismatch between query and chunk raises DimensionMismatchError."""
        query_vec = [1.0, 0.0, 0.0]  # 3-dim
        chunks = [
            {
                "text": "Chunk with 2-dim vector",
                "metadata": {"source": "doc.pdf"},
                "embedding": [1.0, 0.0],  # 2-dim
                "embedding_model": "text-embedding-3-small",
            }
        ]

        with pytest.raises(DimensionMismatchError, match="Vector dimensions must match"):
            rank_chunks(
                query=query_vec,
                chunk_records=chunks,
                validate_model=False,
            )


class TestSanityTestRunner:
    """Test suite for the deterministic sanity test runner and reporting."""

    def test_sanity_runner_all_passing(self) -> None:
        """Verify runner marks all tests PASS when top sources match expected sources."""
        mock_service = MagicMock()
        mock_service.model = "text-embedding-3-small"

        # Provide distinct query embeddings matching the prototype vectors in SAMPLE_CHUNK_RECORDS
        query_embeddings = {
            "What is the advisory fee structure and billing schedule?": [0.95, 0.05, 0.02, 0.01, 0.01],
            "When does the bond fund mature and what is its annual yield?": [0.03, 0.96, 0.04, 0.02, 0.01],
            "How is customer identity verified under KYC and AML rules?": [0.02, 0.03, 0.95, 0.04, 0.02],
            "What are the account security requirements for password resets?": [0.01, 0.02, 0.03, 0.97, 0.03],
            "What is the penalty for early withdrawal from fixed term deposits?": [0.02, 0.01, 0.02, 0.02, 0.96],
        }
        mock_service.embed_query.side_effect = lambda q: query_embeddings.get(q, [0.0, 0.0, 0.0, 0.0, 0.0])

        results = run_sanity_tests(
            test_cases=SAMPLE_SANITY_TEST_CASES,
            chunk_records=SAMPLE_CHUNK_RECORDS,
            embedding_service=mock_service,
        )

        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0
        assert results["pass_rate"] == 100.0

        for r in results["results"]:
            assert r["passed"] is True
            assert r["top_source"] == r["expected_source"]
            assert r["diagnostics"] is None

    def test_sanity_runner_handles_failures_with_diagnostics(self) -> None:
        """Verify runner identifies failures and generates helpful diagnostic information."""
        mock_service = MagicMock()
        mock_service.model = "text-embedding-3-small"
        # Always return fee schedule vector
        mock_service.embed_query.return_value = [0.95, 0.05, 0.02, 0.01, 0.01]

        failing_cases = [
            {
                "query": "When does the bond fund mature?",
                "expected_source": "fund-factsheet.pdf",  # But top will be fee-schedule.pdf
            },
            {
                "query": "Where is the branch located?",
                "expected_source": "non-existent-source.pdf",  # Source missing entirely
            },
        ]

        results = run_sanity_tests(
            test_cases=failing_cases,
            chunk_records=SAMPLE_CHUNK_RECORDS,
            embedding_service=mock_service,
        )

        assert results["total"] == 2
        assert results["passed"] == 0
        assert results["failed"] == 2
        assert results["pass_rate"] == 0.0

        # Check diagnostics on mismatched top source
        assert results["results"][0]["passed"] is False
        assert "outranked expected source" in results["results"][0]["diagnostics"]

        # Check diagnostics on missing expected source
        assert results["results"][1]["passed"] is False
        assert "not present in the chunk corpus" in results["results"][1]["diagnostics"]

    def test_report_generation(self) -> None:
        """Verify formatted sanity report includes all required sections and summary counts."""
        mock_results = {
            "total": 2,
            "passed": 1,
            "failed": 1,
            "pass_rate": 50.0,
            "results": [
                {
                    "query": "What is the fee?",
                    "expected_source": "fee.pdf",
                    "top_source": "fee.pdf",
                    "top_score": 0.8912,
                    "passed": True,
                    "diagnostics": None,
                },
                {
                    "query": "When does it mature?",
                    "expected_source": "fund.pdf",
                    "top_source": "marketing.pdf",
                    "top_score": 0.7654,
                    "passed": False,
                    "diagnostics": "Top source marketing.pdf outranked fund.pdf",
                },
            ],
        }

        report = generate_sanity_report(mock_results)

        assert "Embedding Sanity Report" in report
        assert "Tests: 2" in report
        assert "Passed: 1" in report
        assert "Failed: 1" in report
        assert "[PASS]" in report
        assert "[FAIL]" in report
        assert "Pass rate: 50.0%" in report
        assert "Diagnostics: Top source marketing.pdf outranked fund.pdf" in report
