"""Unit and integration tests for Context Injection and Prompt Augmentation."""

import pytest
from unittest.mock import AsyncMock, patch

from src.core.config import Settings, settings
from src.services.context_injection import (
    assemble_context,
    build_prompt,
    calculate_effective_context_budget,
    count_tokens,
    format_chunk,
    format_prompt_overview,
    DEFAULT_CHUNK_DELIMITER,
    NO_CONTEXT_FALLBACK_TEXT,
)
from src.services.llm import generate_grounded_answer


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_candidate_chunks():
    """Standard sample retrieved chunks with diverse metadata and ranking."""
    return [
        {
            "rank": 1,
            "score": 0.94,
            "text": "Marcus paid the advisory fee on 20 August 2026 via direct bank transfer.",
            "metadata": {
                "source": "client-payment-record.pdf",
                "chunk_index": 12,
                "document_id": "doc_pay_001",
                "approval_status": "approved",
            },
            "id": "doc_pay_001:12",
        },
        {
            "rank": 2,
            "score": 0.88,
            "text": "The annual portfolio advisory fee schedule is 0.75% of assets under management.",
            "metadata": {
                "source": "fee-schedule.pdf",
                "chunk_index": 0,
                "document_id": "doc_fee_001",
                "approval_status": "approved",
            },
            "id": "doc_fee_001:0",
        },
        {
            "rank": 3,
            "score": 0.82,
            "text": "General Advisory Terms: Invoices are generated quarterly in arrears.",
            "metadata": {
                "source": "advisory-agreement.md",
                # Note: chunk_index omitted to test graceful fallback
                "document_id": "doc_terms_001",
                "approval_status": "approved",
            },
            "id": "doc_terms_001:none",
        },
    ]


# ==============================================================================
# 1. Chunk Formatting Tests
# ==============================================================================

class TestChunkFormatting:
    """Tests for format_chunk with source markers and metadata handling."""

    def test_format_chunk_with_index(self):
        """Verify format_chunk includes source document name and chunk index marker."""
        chunk = {
            "text": "Marcus paid the advisory fee on 20 August.",
            "metadata": {
                "source": "client-payment-record.pdf",
                "chunk_index": 12,
            },
        }
        formatted = format_chunk(1, chunk)
        expected_marker = "[1] client-payment-record.pdf#12"
        assert formatted.startswith(expected_marker)
        assert "Marcus paid the advisory fee on 20 August." in formatted

    def test_format_chunk_missing_index(self):
        """Verify format_chunk handles missing chunk_index safely without #None."""
        chunk = {
            "text": "General compliance policy statement.",
            "metadata": {
                "source": "compliance-policy.pdf",
                "chunk_index": None,
            },
        }
        formatted = format_chunk(2, chunk)
        assert formatted.startswith("[2] compliance-policy.pdf")
        assert "#" not in formatted.split("\n")[0]
        assert "General compliance policy statement." in formatted

    def test_format_chunk_empty_metadata_fallback(self):
        """Verify format_chunk uses safe fallback when metadata is missing."""
        chunk = {"text": "Some financial text without metadata"}
        formatted = format_chunk(3, chunk)
        assert formatted.startswith("[3] source-document")
        assert "Some financial text without metadata" in formatted

    def test_format_chunk_preserves_object_structure(self):
        """Verify format_chunk supports objects with text and metadata attributes."""
        class MockChunk:
            text = "Object chunk content."
            metadata = {"source": "annual-report.pdf", "chunk_index": 4}

        formatted = format_chunk(1, MockChunk())
        assert formatted.startswith("[1] annual-report.pdf#4")
        assert "Object chunk content." in formatted


# ==============================================================================
# 2. Token Counting Tests
# ==============================================================================

class TestTokenCounting:
    """Tests for token counting abstraction across empty, short, and long texts."""

    def test_count_tokens_empty(self):
        """Verify empty string returns 0 tokens."""
        assert count_tokens("") == 0
        assert count_tokens(None) == 0  # type: ignore

    def test_count_tokens_short(self):
        """Verify short financial sentence returns realistic positive token count."""
        text = "What is the exit load for Fund A?"
        tokens = count_tokens(text)
        assert isinstance(tokens, int)
        assert 5 <= tokens <= 15

    def test_count_tokens_longer_text(self):
        """Verify longer text scales appropriately."""
        short_text = "Advisory fee is 1.0%."
        long_text = short_text * 20
        assert count_tokens(long_text) > count_tokens(short_text) * 15

    def test_count_tokens_fallback_handling(self):
        """Verify fallback behavior if encoding name is invalid."""
        with patch("tiktoken.get_encoding", side_effect=Exception("Encoding not found")):
            tokens = count_tokens("Test financial query string with multiple words.")
            assert tokens > 0


# ==============================================================================
# 3. Context Assembly & Token Budget Tests
# ==============================================================================

class TestContextAssembly:
    """Tests for assemble_context with token-budget control and delimiter preservation."""

    def test_assemble_context_in_order(self, sample_candidate_chunks):
        """Verify chunks are assembled in their given ranking order separated by delimiter."""
        result = assemble_context(sample_candidate_chunks, max_context_tokens=5000)

        assert len(result["selected_chunks"]) == 3
        assert len(result["sources_used"]) == 3
        assert result["source_markers"] == ["[1]", "[2]", "[3]"]
        assert result["context_tokens"] > 0

        # Check delimiter presence
        assert DEFAULT_CHUNK_DELIMITER in result["context"]
        assert "[1] client-payment-record.pdf#12" in result["context"]
        assert "[2] fee-schedule.pdf#0" in result["context"]
        assert "[3] advisory-agreement.md" in result["context"]

    def test_assemble_context_stops_before_budget_exceeded(self, sample_candidate_chunks):
        """Verify context stops adding chunks before exceeding max_context_tokens."""
        # Calculate tokens for the first chunk
        c1_tokens = count_tokens(format_chunk(1, sample_candidate_chunks[0]))
        # Set budget to accommodate only chunk 1 plus a tiny margin
        tight_budget = c1_tokens + 5

        result = assemble_context(sample_candidate_chunks, max_context_tokens=tight_budget)

        assert len(result["selected_chunks"]) == 1
        assert result["context_tokens"] <= tight_budget
        assert result["selected_chunks"][0]["id"] == "doc_pay_001:12"
        assert result["source_markers"] == ["[1]"]

    def test_assemble_context_oversized_chunk_skipped(self):
        """Verify an individual chunk exceeding total budget is safely skipped without crash."""
        chunks = [
            {
                "id": "giant_chunk",
                "text": "Extremely verbose detailed disclosure statement " * 100,
                "metadata": {"source": "huge.pdf", "chunk_index": 1},
            },
            {
                "id": "normal_chunk",
                "text": "Compact fee schedule 1.0%.",
                "metadata": {"source": "fee.pdf", "chunk_index": 0},
            },
        ]
        # Set budget small enough that giant_chunk exceeds it, but normal_chunk fits
        result = assemble_context(chunks, max_context_tokens=30)
        assert len(result["selected_chunks"]) == 1
        assert result["selected_chunks"][0]["id"] == "normal_chunk"
        assert "[2] fee.pdf#0" in result["context"]

    def test_assemble_context_empty_chunks(self):
        """Verify empty candidate list returns empty context and 0 tokens."""
        result = assemble_context([], max_context_tokens=5000)
        assert result["context"] == ""
        assert result["context_tokens"] == 0
        assert result["selected_chunks"] == []
        assert result["sources_used"] == []
        assert result["source_markers"] == []

    def test_assemble_context_metadata_preservation(self, sample_candidate_chunks):
        """Verify metadata from all selected chunks is preserved for citation generation."""
        result = assemble_context(sample_candidate_chunks, max_context_tokens=5000)
        sources = result["sources_used"]
        assert len(sources) == 3
        assert sources[0]["source"] == "client-payment-record.pdf"
        assert sources[0]["chunk_index"] == 12
        assert sources[0]["marker"] == "[1]"
        assert sources[1]["source"] == "fee-schedule.pdf"
        assert sources[1]["chunk_index"] == 0
        assert sources[1]["marker"] == "[2]"


# ==============================================================================
# 4. Prompt Augmentation & Grounding Rules Tests
# ==============================================================================

class TestPromptAugmentation:
    """Tests for build_prompt and safety/compliance instruction enforcement."""

    def test_build_prompt_structure_separation(self, sample_candidate_chunks):
        """Verify prompt cleanly separates System Instructions, Context, and Question."""
        question = "What evidence supports the advisory fee charged to Marcus?"
        prompt_info = build_prompt(question, sample_candidate_chunks, max_context_tokens=5000)

        prompt = prompt_info["prompt"]
        assert "You are a compliance-grounded financial advisory assistant." in prompt
        assert "Context:\n[1] client-payment-record.pdf#12" in prompt
        assert "Question:\nWhat evidence supports the advisory fee charged to Marcus?" in prompt

        # Verify structured prompt dictionary keys
        assert "prompt" in prompt_info
        assert "system_instruction" in prompt_info
        assert "user_prompt" in prompt_info
        assert "context" in prompt_info
        assert "context_tokens" in prompt_info
        assert "selected_chunks" in prompt_info
        assert "sources_used" in prompt_info
        assert "source_markers" in prompt_info
        assert prompt_info["question"] == question

    def test_build_prompt_missing_evidence_instruction(self):
        """Verify the exact missing evidence fallback clause is present."""
        prompt_info = build_prompt("What is the penalty fee?", [])
        system_instr = prompt_info["system_instruction"]
        assert "I don't have enough information in the provided context." in system_instr

    def test_build_prompt_citation_marker_instruction(self):
        """Verify citation marker instruction is present."""
        prompt_info = build_prompt("What is the fee?", [])
        system_instr = prompt_info["system_instruction"]
        assert "Cite supporting evidence using source markers such as [1] or [2]." in system_instr

    def test_build_prompt_conflicting_sources_instruction(self):
        """Verify instruction to identify conflicts is present."""
        prompt_info = build_prompt("Compare the fees", [])
        system_instr = prompt_info["system_instruction"]
        assert "If sources conflict, clearly identify the conflict" in system_instr

    def test_build_prompt_empty_context_fallback(self):
        """Verify build_prompt displays fallback text when no chunks are retrieved."""
        prompt_info = build_prompt("What is the fee?", [])
        assert NO_CONTEXT_FALLBACK_TEXT in prompt_info["user_prompt"]
        assert NO_CONTEXT_FALLBACK_TEXT in prompt_info["prompt"]
        assert prompt_info["context_tokens"] == 0

    def test_build_prompt_empty_question_rejected(self):
        """Verify empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            build_prompt("   ", [])

    def test_format_prompt_overview(self, sample_candidate_chunks):
        """Verify format_prompt_overview generates structured summary report."""
        prompt_info = build_prompt("What is the advisory fee?", sample_candidate_chunks)
        overview = format_prompt_overview(prompt_info)
        assert "Augmented Prompt Summary" in overview
        assert "Question: What is the advisory fee?" in overview
        assert "[1]" in overview
        assert "client-payment-record.pdf#12" in overview


# ==============================================================================
# 5. Token Budget Reservation Configuration Tests
# ==============================================================================

class TestBudgetConfiguration:
    """Tests for dynamic token reservation formula and settings integration."""

    def test_budget_reservation_calculation(self):
        """Verify effective budget calculation respects model context and reserves."""
        # 8192 total - 1500 answer - 800 instruction = 5892 max context
        budget = calculate_effective_context_budget(
            max_model_tokens=8192,
            reserved_answer_tokens=1500,
            reserved_instruction_tokens=800,
            configured_context_tokens=5000,
        )
        assert budget == 5000

        # When configured exceeds available ceiling
        tight_budget = calculate_effective_context_budget(
            max_model_tokens=4000,
            reserved_answer_tokens=1500,
            reserved_instruction_tokens=800,
            configured_context_tokens=5000,
        )
        # 4000 - 2300 = 1700
        assert tight_budget == 1700

    def test_config_settings_defaults(self):
        """Verify Settings contains the new context injection configuration fields."""
        cfg = Settings()
        assert cfg.MAX_MODEL_CONTEXT_TOKENS >= 4096
        assert cfg.MAX_CONTEXT_TOKENS == 5000
        assert cfg.RESERVED_ANSWER_TOKENS == 1500
        assert cfg.RESERVED_INSTRUCTION_TOKENS == 800


# ==============================================================================
# 6. End-to-End RAG Integration with Mocked LLM Service
# ==============================================================================

class TestEndToEndRAGIntegration:
    """Tests for generate_grounded_answer end-to-end integration."""

    @pytest.mark.anyio
    async def test_generate_grounded_answer_integration(self, sample_candidate_chunks):
        """Verify generate_grounded_answer connects context injection to LLM API call."""
        mock_response = "According to [1], Marcus paid the advisory fee on 20 August 2026."

        with patch("src.services.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await generate_grounded_answer(
                question="When was the advisory fee paid?",
                retrieved_chunks=sample_candidate_chunks,
            )

            assert result["answer"] == mock_response
            assert len(result["selected_chunks"]) == 3
            assert result["source_markers"] == ["[1]", "[2]", "[3]"]
            assert len(result["sources_used"]) == 3
            assert "prompt_info" in result
            assert result["context_tokens"] > 0

            # Verify generate_answer was invoked with assembled context
            mock_llm.assert_called_once()
            call_kwargs = mock_llm.call_args.kwargs
            assert call_kwargs["question"] == "When was the advisory fee paid?"
            assert "[1] client-payment-record.pdf#12" in call_kwargs["context"]
