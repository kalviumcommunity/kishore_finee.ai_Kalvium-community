"""Unit and integration tests for Conversational RAG and Follow-up Query Rewriting."""

import pytest
from unittest.mock import AsyncMock, patch

from src.core.config import Settings, settings
from src.services.conversational_rag import (
    ConversationSession,
    conversational_answer,
    format_conversation_history,
    rewrite_followup,
    trim_conversation_history,
    validate_rewritten_query,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_history():
    """Standard multi-turn conversation history."""
    return [
        {
            "role": "user",
            "content": "What evidence is required for project submission?",
        },
        {
            "role": "assistant",
            "content": "The submission needs a PR link, sample output, and a video explanation.",
        },
    ]


@pytest.fixture
def submission_chunks():
    """Strong chunks regarding project submission requirements."""
    return [
        {
            "rank": 1,
            "score": 0.95,
            "text": "Project Submission Guidelines: A 3-minute video explanation walking through code changes and architecture is mandatory.",
            "metadata": {"source": "submission-guide.md", "chunk_index": 2},
            "id": "doc_sub_01:2",
        },
        {
            "rank": 2,
            "score": 0.89,
            "text": "Sprint 2 Assessment Criteria: Video demonstration must cover unit tests and API readback validation.",
            "metadata": {"source": "sprint2-rubric.pdf", "chunk_index": 1},
            "id": "doc_rubric_02:1",
        },
    ]


# ==============================================================================
# 1. History Formatting and Trimming Tests
# ==============================================================================

class TestConversationHistoryManagement:
    """Tests for history formatting, rolling turn bounds, and token budgets."""

    def test_format_conversation_history(self, sample_history):
        """Format history list into readable User/Assistant dialogue."""
        formatted = format_conversation_history(sample_history)
        assert "User: What evidence is required for project submission?" in formatted
        assert "Assistant: The submission needs a PR link, sample output, and a video explanation." in formatted

    def test_format_empty_history(self):
        """Empty history returns clear placeholder."""
        assert format_conversation_history([]) == "[No prior conversation history]"

    def test_history_trimming_by_turn_limit(self):
        """Trims history when exceeding max_turns (keeps recent turns)."""
        history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
            {"role": "user", "content": "Question 3"},
            {"role": "assistant", "content": "Answer 3"},
        ]
        # max_turns=2 -> keeps 4 messages (Question 2, Answer 2, Question 3, Answer 3)
        trimmed = trim_conversation_history(history, max_turns=2)
        assert len(trimmed) == 4
        assert trimmed[0]["content"] == "Question 2"
        assert trimmed[-1]["content"] == "Answer 3"

    def test_history_trimming_by_token_budget(self):
        """Trims older turns when history exceeds token budget."""
        history = [
            {"role": "user", "content": "Long detailed financial question with many background facts " * 10},
            {"role": "assistant", "content": "Long comprehensive explanation " * 10},
            {"role": "user", "content": "Recent question?"},
            {"role": "assistant", "content": "Recent answer."},
        ]
        # Set token budget tight so only recent turn fits
        trimmed = trim_conversation_history(history, max_tokens=25)
        assert len(trimmed) <= 2
        assert "Recent" in trimmed[-1]["content"]


# ==============================================================================
# 2. Query Rewriting Validation & Sanitization Tests
# ==============================================================================

class TestQueryRewritingValidation:
    """Tests for validate_rewritten_query sanitization and safe fallbacks."""

    def test_validate_clean_query(self):
        """Standard rewritten query is trimmed and cleaned."""
        raw = '  "What video explanation is required for project submission?"  '
        assert validate_rewritten_query(raw, "original") == "What video explanation is required for project submission?"

    def test_validate_query_strips_prefix_labels(self):
        """Strips 'Standalone Search Query:' and similar prefix labels."""
        raw = "Standalone Search Query: What video explanation is required for project submission?"
        assert validate_rewritten_query(raw, "original") == "What video explanation is required for project submission?"

        raw2 = "Query: When is the fee due?"
        assert validate_rewritten_query(raw2, "original") == "When is the fee due?"

    def test_validate_rejects_empty_or_whitespace(self):
        """Falls back to original question if rewritten output is empty."""
        assert validate_rewritten_query("", "What about the video?") == "What about the video?"
        assert validate_rewritten_query("   ", "What about the video?") == "What about the video?"

    def test_validate_rejects_verbose_answers(self):
        """Rejects outputs that appear to answer the question with multi-paragraph text."""
        verbose_answer = (
            "Based on the knowledge base, project submissions require three items:\n\n"
            "1. A GitHub Pull Request link\n"
            "2. Sample outputs\n"
            "3. A video walk-through."
        )
        assert validate_rewritten_query(verbose_answer, "What about the video?") == "What about the video?"


# ==============================================================================
# 3. Follow-Up Query Rewriting Engine Tests
# ==============================================================================

class TestFollowupQueryRewriting:
    """Tests for rewrite_followup with pronoun resolution and error fallbacks."""

    @pytest.mark.anyio
    async def test_empty_history_returns_original_question(self):
        """1. Empty history returns original question immediately without API call."""
        res = await rewrite_followup(history=[], question="What is the advisory fee rate?")
        assert res == "What is the advisory fee rate?"

    @pytest.mark.anyio
    async def test_followup_question_with_mock_llm(self, sample_history):
        """2 & 3. Follow-up query rewritten into standalone query via LLM call."""
        mock_rewritten = "What video explanation is required for project submission?"

        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": mock_rewritten}}]
        }

        with patch.object(settings, "OPENAI_API_KEY", "test-key"), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):

            result = await rewrite_followup(
                history=sample_history,
                question="What about the video?",
            )
            assert result == mock_rewritten

    @pytest.mark.anyio
    async def test_followup_pronoun_resolution_heuristic_fallback(self, sample_history):
        """4 & 5. Heuristic fallback resolves 'What about the video?' when API is offline."""
        with patch.object(settings, "OPENAI_API_KEY", None), patch.object(settings, "GROQ_API_KEY", None):
            result = await rewrite_followup(
                history=sample_history,
                question="What about the video?",
            )
            assert "video" in result.lower()
            assert "project submission" in result.lower()

    @pytest.mark.anyio
    async def test_followup_pronoun_it_resolution(self, sample_history):
        """Resolves 'Does it apply to Sprint 2?' referencing prior submission topic."""
        with patch.object(settings, "OPENAI_API_KEY", None), patch.object(settings, "GROQ_API_KEY", None):
            result = await rewrite_followup(
                history=sample_history,
                question="Does it apply to Sprint 2?",
            )
            assert "sprint 2" in result.lower()
            assert "project submission" in result.lower() or "apply" in result.lower()

    @pytest.mark.anyio
    async def test_followup_pronoun_that_resolution(self, sample_history):
        """Resolves 'Can you explain that?' with context anchor."""
        with patch.object(settings, "OPENAI_API_KEY", None), patch.object(settings, "GROQ_API_KEY", None):
            result = await rewrite_followup(
                history=sample_history,
                question="Can you explain that in more detail?",
            )
            assert "project submission" in result.lower() or "explain" in result.lower()

    @pytest.mark.anyio
    async def test_llm_rewrite_failure_falls_back_safely(self, sample_history):
        """10. LLM HTTP failure falls back safely to the original question or heuristic."""
        with patch.object(settings, "OPENAI_API_KEY", "test-key"), \
             patch("httpx.AsyncClient.post", side_effect=Exception("Connection timeout")):
            result = await rewrite_followup(
                history=sample_history,
                question="What about the video?",
            )
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.anyio
    async def test_empty_question_raises_value_error(self):
        """Empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            await rewrite_followup(history=[], question="   ")

    def test_config_conversational_defaults(self):
        """Verify Settings contains the new conversational RAG configuration fields."""
        cfg = Settings()
        assert cfg.MAX_CONVERSATION_TURNS == 5
        assert cfg.MAX_HISTORY_TOKENS == 1000
        assert cfg.QUERY_REWRITE_MODEL is None


# ==============================================================================
# 4. Conversational RAG Pipeline Integration Tests
# ==============================================================================

class TestConversationalRAGPipeline:
    """Tests for conversational_answer end-to-end multi-turn execution."""

    @pytest.mark.anyio
    async def test_conversational_turn_uses_rewritten_query_for_retrieval(self, submission_chunks):
        """13 & 14. Retrieval receives the rewritten query, while answer generation answers the user question."""
        history = [
            {"role": "user", "content": "What evidence is required for project submission?"},
            {"role": "assistant", "content": "You need a PR link, outputs, and video."},
        ]

        with patch("src.services.conversational_rag.rewrite_followup", new_callable=AsyncMock) as mock_rewrite, \
             patch("src.services.conversational_rag.guarded_answer", new_callable=AsyncMock) as mock_guard:

            mock_rewrite.return_value = "What video explanation is required for project submission?"
            mock_guard.return_value = {
                "answer": "The video explanation must be 3 minutes walking through changes [1].",
                "sources": [{"marker": "[1]", "source": "submission-guide.md", "chunk_index": 2}],
                "status": "answered",
                "metrics": {"top_score": 0.95, "llm_called": True},
            }

            result = await conversational_answer(
                history=history,
                user_question="What about the video?",
                chunks=submission_chunks,
            )

            assert result["rewritten_query"] == "What video explanation is required for project submission?"
            assert result["original_question"] == "What about the video?"
            assert result["status"] == "answered"
            assert len(result["sources"]) == 1

            # 17 & 18. Verify user message in history is the ORIGINAL question (not the rewritten query)
            assert len(history) == 4
            assert history[2]["role"] == "user"
            assert history[2]["content"] == "What about the video?"
            assert history[3]["role"] == "assistant"
            assert "The video explanation" in history[3]["content"]

    @pytest.mark.anyio
    async def test_weak_retrieval_triggers_safe_refusal(self):
        """15. Weak retrieval on rewritten query returns safe refusal without calling LLM."""
        history = []
        weak_chunks = [
            {"score": 0.45, "text": "Unrelated cafeteria notice", "metadata": {"source": "cafeteria.txt"}}
        ]

        result = await conversational_answer(
            history=history,
            user_question="What is the parking permit fee for Sprint 2?",
            chunks=weak_chunks,
            min_top_score=0.72,
        )

        assert result["status"] == "refused_weak_context"
        assert result["answer"] == settings.SAFE_REFUSAL_MESSAGE
        assert result["sources"] == []
        assert len(history) == 2
        assert history[0]["content"] == "What is the parking permit fee for Sprint 2?"


# ==============================================================================
# 5. ConversationSession Class Tests
# ==============================================================================

class TestConversationSession:
    """Tests for isolated ConversationSession state management."""

    @pytest.mark.anyio
    async def test_session_isolation_and_multi_turn(self, submission_chunks):
        """20. Multiple sessions maintain isolated conversation history."""
        session_a = ConversationSession(session_id="session_alpha")
        session_b = ConversationSession(session_id="session_beta")

        with patch("src.services.conversational_rag.guarded_answer", new_callable=AsyncMock) as mock_guard:
            mock_guard.return_value = {
                "answer": "Submission requires a video walk-through [1].",
                "sources": [{"marker": "[1]", "source": "guide.md"}],
                "status": "answered",
                "metrics": {"top_score": 0.95, "llm_called": True},
            }

            await session_a.ask("What is required for submission?", chunks=submission_chunks)

            # Session A should have 1 turn (2 messages)
            assert len(session_a.history) == 2
            # Session B must remain completely empty and isolated
            assert len(session_b.history) == 0

            session_a.clear()
            assert len(session_a.history) == 0

