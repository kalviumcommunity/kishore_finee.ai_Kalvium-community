"""Unit and integration tests for Retrieval Guardrails and Safe Refusal."""

import pytest
from unittest.mock import AsyncMock, patch

from src.core.config import Settings, settings
from src.services.guardrails import (
    evaluate_retrieval_strength,
    format_guardrail_report,
    get_chunk_score,
    guarded_answer,
    retrieval_is_strong,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def strong_chunks():
    """Retrieved chunks with high relevance scores above threshold (0.72)."""
    return [
        {
            "rank": 1,
            "score": 0.94,
            "text": "Marcus paid the advisory fee on 20 August 2026 via direct bank transfer.",
            "metadata": {"source": "client-billing-records.pdf", "chunk_index": 1},
            "id": "doc_pay_001:1",
        },
        {
            "rank": 2,
            "score": 0.88,
            "text": "The annual portfolio advisory fee schedule is 0.75% of assets under management.",
            "metadata": {"source": "fee-schedule.pdf", "chunk_index": 0},
            "id": "doc_fee_001:0",
        },
    ]


@pytest.fixture
def weak_chunks():
    """Retrieved chunks with low relevance scores below threshold (0.72)."""
    return [
        {
            "rank": 1,
            "score": 0.58,
            "text": "General cafeteria menu and lunch discount hours for office employees.",
            "metadata": {"source": "cafeteria.txt", "chunk_index": 0},
            "id": "doc_cafe:0",
        },
        {
            "rank": 2,
            "score": 0.42,
            "text": "Parking garage maintenance schedule for Building B.",
            "metadata": {"source": "parking.txt", "chunk_index": 0},
            "id": "doc_park:0",
        },
    ]


# ==============================================================================
# 1. Score Extraction Tests
# ==============================================================================

class TestScoreExtraction:
    """Tests for resilient get_chunk_score helper."""

    def test_get_chunk_score_standard(self):
        """Extract score from standard dict."""
        assert get_chunk_score({"score": 0.85}) == 0.85

    def test_get_chunk_score_vector_score_alias(self):
        """Extract score from vector_score alias."""
        assert get_chunk_score({"vector_score": 0.91}) == 0.91

    def test_get_chunk_score_missing(self):
        """Return 0.0 when score is missing."""
        assert get_chunk_score({"text": "No score here"}) == 0.0

    def test_get_chunk_score_non_numeric(self):
        """Return 0.0 when score is non-numeric string or invalid object."""
        assert get_chunk_score({"score": "invalid"}) == 0.0
        assert get_chunk_score({"score": None}) == 0.0

    def test_get_chunk_score_object(self):
        """Extract score from chunk object attribute."""
        class MockChunk:
            score = 0.78
        assert get_chunk_score(MockChunk()) == 0.78


# ==============================================================================
# 2. Retrieval Strength Validation Tests
# ==============================================================================

class TestRetrievalStrength:
    """Tests for retrieval_is_strong quality validation."""

    def test_empty_chunk_list_returns_false(self):
        """1. Empty chunk list returns False."""
        assert retrieval_is_strong([]) is False
        assert retrieval_is_strong(None) is False

    def test_one_chunk_below_threshold(self):
        """2. One chunk below MIN_TOP_SCORE (0.72) returns False."""
        chunks = [{"score": 0.65, "text": "Weak chunk"}]
        assert retrieval_is_strong(chunks, min_top_score=0.72) is False

    def test_one_chunk_equal_threshold(self):
        """3. One chunk exactly equal to threshold returns True."""
        chunks = [{"score": 0.72, "text": "Borderline chunk"}]
        assert retrieval_is_strong(chunks, min_top_score=0.72, min_supporting_chunks=1) is True

    def test_one_chunk_above_threshold(self):
        """4. One chunk above threshold returns True."""
        chunks = [{"score": 0.92, "text": "Strong chunk"}]
        assert retrieval_is_strong(chunks, min_top_score=0.72, min_supporting_chunks=1) is True

    def test_multiple_chunks_single_strong(self):
        """5. Multiple chunks where only one is strong."""
        chunks = [
            {"score": 0.90, "text": "Strong chunk 1"},
            {"score": 0.40, "text": "Weak chunk 2"},
            {"score": 0.35, "text": "Weak chunk 3"},
        ]
        # With min_supporting_chunks = 1 -> True
        assert retrieval_is_strong(chunks, min_top_score=0.72, min_supporting_chunks=1) is True
        # With min_supporting_chunks = 2 -> False
        assert retrieval_is_strong(chunks, min_top_score=0.72, min_supporting_chunks=2) is False

    def test_multiple_strong_chunks(self, strong_chunks):
        """6. Multiple strong chunks above threshold returns True."""
        assert retrieval_is_strong(strong_chunks, min_top_score=0.72, min_supporting_chunks=2) is True

    def test_missing_and_invalid_score_handled_safely(self):
        """7 & 8. Missing and invalid score fields handled safely without crash."""
        chunks = [
            {"text": "Chunk with no score"},
            {"score": "N/A", "text": "Chunk with non-numeric score"},
        ]
        assert retrieval_is_strong(chunks, min_top_score=0.72) is False


# ==============================================================================
# 3. Retrieval Evaluation & Refusal Reasons Tests
# ==============================================================================

class TestEvaluateRetrievalStrength:
    """Tests for evaluate_retrieval_strength status classification."""

    def test_refused_empty_context(self):
        """Classify empty chunk list as refused_empty_context."""
        res = evaluate_retrieval_strength([])
        assert res["is_strong"] is False
        assert res["status"] == "refused_empty_context"
        assert res["top_score"] == 0.0
        assert res["refusal_reason"] is not None

    def test_refused_weak_context(self, weak_chunks):
        """Classify low-scoring chunks as refused_weak_context."""
        res = evaluate_retrieval_strength(weak_chunks, min_top_score=0.72)
        assert res["is_strong"] is False
        assert res["status"] == "refused_weak_context"
        assert res["top_score"] == 0.58
        assert "below minimum threshold" in res["refusal_reason"]

    def test_refused_insufficient_support(self):
        """Classify when top score meets threshold but count of strong chunks is insufficient."""
        chunks = [
            {"score": 0.85, "text": "One strong chunk"},
            {"score": 0.40, "text": "Weak chunk"},
        ]
        res = evaluate_retrieval_strength(chunks, min_top_score=0.72, min_supporting_chunks=2)
        assert res["is_strong"] is False
        assert res["status"] == "refused_insufficient_support"
        assert "minimum 2 required" in res["refusal_reason"]

    def test_answered_status(self, strong_chunks):
        """Classify strong retrieval as answered."""
        res = evaluate_retrieval_strength(strong_chunks, min_top_score=0.72, min_supporting_chunks=1)
        assert res["is_strong"] is True
        assert res["status"] == "answered"
        assert res["top_score"] == 0.94
        assert res["refusal_reason"] is None


# ==============================================================================
# 4. Guarded Answer Pipeline & Pre-LLM Refusal Tests
# ==============================================================================

class TestGuardedAnswerPipeline:
    """Tests for guarded_answer pipeline execution, LLM call prevention, and citation preservation."""

    @pytest.mark.anyio
    async def test_weak_retrieval_does_not_call_llm(self, weak_chunks):
        """9. Weak retrieval returns safe refusal and DOES NOT invoke LLM service."""
        with patch("src.services.llm.generate_grounded_answer", new_callable=AsyncMock) as mock_llm:
            result = await guarded_answer(
                question="What is the cafeteria lunch menu?",
                chunks=weak_chunks,
                min_top_score=0.72,
            )

            # Assert LLM was never called
            mock_llm.assert_not_called()

            # Assert structured refusal response
            assert result["status"] == "refused_weak_context"
            assert result["answer"] == settings.SAFE_REFUSAL_MESSAGE
            assert result["sources"] == []
            assert result["metrics"]["llm_called"] is False
            assert result["metrics"]["top_score"] == 0.58

    @pytest.mark.anyio
    async def test_empty_retrieval_does_not_call_llm(self):
        """10. Empty retrieval returns safe refusal and DOES NOT invoke LLM service."""
        with patch("src.services.llm.generate_grounded_answer", new_callable=AsyncMock) as mock_llm:
            result = await guarded_answer(
                question="Unknown topic query",
                chunks=[],
            )

            mock_llm.assert_not_called()
            assert result["status"] == "refused_empty_context"
            assert result["sources"] == []
            assert result["metrics"]["llm_called"] is False

    @pytest.mark.anyio
    async def test_strong_retrieval_calls_llm_once(self, strong_chunks):
        """11 & 12. Strong retrieval calls LLM service exactly once and returns answered status."""
        mock_grounded_response = {
            "answer": "Marcus paid the fee on 20 August 2026 [1].",
            "sources_used": [
                {"marker": "[1]", "source": "client-billing-records.pdf", "chunk_index": 1}
            ],
            "selected_chunks": strong_chunks,
            "source_markers": ["[1]", "[2]"],
            "context": "Assembled context...",
            "context_tokens": 85,
            "prompt_info": {"prompt": "Full prompt..."},
        }

        with patch("src.services.llm.generate_grounded_answer", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_grounded_response

            result = await guarded_answer(
                question="When was the advisory fee billed?",
                chunks=strong_chunks,
                min_top_score=0.72,
            )

            # Assert LLM was called exactly once
            mock_llm.assert_called_once()

            # Assert answered status and citation preservation
            assert result["status"] == "answered"
            assert result["answer"] == "Marcus paid the fee on 20 August 2026 [1]."
            assert len(result["sources"]) == 1
            assert result["sources"][0]["source"] == "client-billing-records.pdf"
            assert result["metrics"]["llm_called"] is True
            assert result["metrics"]["top_score"] == 0.94

    @pytest.mark.anyio
    async def test_empty_question_rejected(self):
        """Verify empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            await guarded_answer("   ", chunks=[])

    def test_format_guardrail_report(self, weak_chunks):
        """Verify format_guardrail_report formats clean diagnostic string."""
        eval_res = {
            "question": "What is the parking schedule?",
            "status": "refused_weak_context",
            "answer": settings.SAFE_REFUSAL_MESSAGE,
            "refusal_reason": "Top retrieval score (0.5800) is below minimum threshold (0.7200).",
            "metrics": {
                "top_score": 0.58,
                "min_top_score": 0.72,
                "supporting_chunks_count": 0,
                "min_supporting_chunks": 1,
                "retrieved_chunks_count": 2,
                "llm_called": False,
            },
            "sources": [],
        }
        report = format_guardrail_report(eval_res)
        assert "Retrieval Guardrail Diagnostic Report" in report
        assert "REFUSED_WEAK_CONTEXT" in report
        assert "LLM Called: False" in report
        assert "Top Retrieval Score: 0.5800" in report
        assert settings.SAFE_REFUSAL_MESSAGE in report

    def test_config_settings_defaults(self):
        """Verify Settings contains the new retrieval guardrails configuration."""
        cfg = Settings()
        assert cfg.MIN_TOP_SCORE == 0.70
        assert cfg.MIN_SUPPORTING_CHUNKS == 1
        assert cfg.RETRIEVAL_TOP_K == 4
        assert "approved knowledge base" in cfg.SAFE_REFUSAL_MESSAGE
