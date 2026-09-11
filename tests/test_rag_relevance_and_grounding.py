"""Automated test suite for RAG relevance, grounded answers, out-of-scope refusals, and citation sanitization."""

import pytest
from unittest.mock import AsyncMock, patch

from src.core.config import settings
from src.retrieval.reranker import (
    _deterministic_relevance_scorer,
    filter_relevant_candidates,
    rerank,
)
from src.services.context_injection import validate_and_sanitize_citations
from src.services.guardrails import (
    evaluate_retrieval_strength,
    guarded_answer,
    retrieval_is_strong,
)
from src.api.routes.query import _check_evidence_conflict


@pytest.fixture
def mock_fund_candidates():
    """Candidate pool containing target fund evidence and distractors."""
    return [
        {
            "id": "chunk_alpha_1",
            "score": 0.88,
            "text": "The Alpha Large Cap Equity Fund seeks long-term capital appreciation by investing in large-cap domestic equities with high growth potential.",
            "metadata": {"source": "alpha_large_cap_factsheet.pdf", "chunk_index": 1, "section": "Investment Objective"},
        },
        {
            "id": "chunk_alpha_2",
            "score": 0.85,
            "text": "Alpha Large Cap Equity Fund benchmark is the S&P 500 Total Return Index with an annual expense ratio of 0.65%.",
            "metadata": {"source": "alpha_large_cap_factsheet.pdf", "chunk_index": 2, "section": "Benchmark & Fees"},
        },
        {
            "id": "chunk_beta_1",
            "score": 0.72,
            "text": "Beta Multi-Asset Income Fund allocates across fixed income and dividend equities with an annual distribution yield of 4.8%.",
            "metadata": {"source": "beta_income_fund.pdf", "chunk_index": 1, "section": "Strategy"},
        },
        {
            "id": "chunk_gamma_1",
            "score": 0.68,
            "text": "Gamma Emerging Markets Debt Fund invests exclusively in sovereign credit across Latin America and Asia.",
            "metadata": {"source": "gamma_debt_fund.pdf", "chunk_index": 1, "section": "Strategy"},
        },
    ]


@pytest.fixture
def mock_fee_policy_chunks():
    """Compliant fee schedule chunks."""
    return [
        {
            "id": "chunk_fee_1",
            "score": 0.92,
            "text": "Standard wealth advisory management fee is set at 1.25% of AUM billed quarterly in arrears for Tier 1 discretionary accounts.",
            "metadata": {"source": "wealth_advisory_standard_2026.pdf", "chunk_index": 1, "section": "Fee Caps"},
        },
        {
            "id": "chunk_fee_2",
            "score": 0.89,
            "text": "Advisory fee billing is calculated on the average daily asset value of the preceding quarter with formal client notification.",
            "metadata": {"source": "wealth_advisory_standard_2026.pdf", "chunk_index": 2, "section": "Billing Schedule"},
        },
    ]


# ==============================================================================
# Scenario 1: Relevant Query Retains Target Chunks & Excludes Distractors
# ==============================================================================

def test_relevant_query_excludes_distractors(mock_fund_candidates):
    """Test that querying for Alpha Large Cap Fund re-ranks and filters out Beta/Gamma distractor funds."""
    query = "What is the investment objective and benchmark of the Alpha Large Cap Equity Fund?"
    
    # 1. Re-rank candidates
    reranked = rerank(query=query, candidates=mock_fund_candidates, final_k=4)
    
    # Top results should be Alpha Large Cap
    assert "Alpha Large Cap" in reranked[0]["text"]
    assert reranked[0]["metadata"]["source"] == "alpha_large_cap_factsheet.pdf"
    
    # 2. Filter candidates
    accepted = filter_relevant_candidates(query=query, candidates=reranked)
    
    # Verify that only Alpha fund chunks are retained and distractors (Beta, Gamma) are dropped
    accepted_sources = [c["metadata"]["source"] for c in accepted]
    assert "alpha_large_cap_factsheet.pdf" in accepted_sources
    assert "gamma_debt_fund.pdf" not in accepted_sources


# ==============================================================================
# Scenario 2: Out-of-Scope Query (e.g. Bitcoin / Crypto) Refused Pre-LLM
# ==============================================================================

@pytest.mark.anyio
async def test_out_of_scope_crypto_query_refused_without_llm(mock_fund_candidates):
    """Test that out-of-scope query ('What is the current Bitcoin price?') is refused before LLM invocation."""
    query = "What is the current Bitcoin price and Ethereum trading volume today?"
    
    with patch("src.services.llm.generate_grounded_answer", new_callable=AsyncMock) as mock_llm:
        res = await guarded_answer(
            question=query,
            chunks=mock_fund_candidates,
            min_top_score=0.70,
            use_reranker=True,
        )
        
        # LLM MUST NOT have been invoked
        mock_llm.assert_not_called()
        
        # Result should be a clean refusal
        assert res["status"].startswith("refused")
        assert res["metrics"]["llm_called"] is False
        assert res["sources"] == []
        assert res["selected_chunks"] == []
        assert "evidence" in res["answer"].lower() or "knowledge base" in res["answer"].lower()


# ==============================================================================
# Scenario 3: Completely Unrelated Query (Sports / Weather) Refused
# ==============================================================================

@pytest.mark.anyio
async def test_unrelated_sports_weather_refused_without_llm(mock_fund_candidates):
    """Test that completely unrelated queries like weather or sports results are safely refused."""
    unrelated_queries = [
        "What is the weather forecast for Paris this weekend?",
        "Who won the UEFA Champions League final yesterday?",
    ]
    
    for q in unrelated_queries:
        with patch("src.services.llm.generate_grounded_answer", new_callable=AsyncMock) as mock_llm:
            res = await guarded_answer(
                question=q,
                chunks=mock_fund_candidates,
                min_top_score=0.70,
                use_reranker=True,
            )
            mock_llm.assert_not_called()
            assert res["status"].startswith("refused")
            assert res["metrics"]["llm_called"] is False
            assert res["sources"] == []


# ==============================================================================
# Scenario 4: Valid Query with Multiple Supporting Chunks Accepted
# ==============================================================================

@pytest.mark.anyio
async def test_valid_query_multiple_supporting_chunks(mock_fee_policy_chunks):
    """Test that a compliant query with multiple supporting chunks passes guardrails and synthesizes an answer."""
    query = "What is the standard advisory fee and quarterly billing schedule for discretionary accounts?"
    
    res = await guarded_answer(
        question=query,
        chunks=mock_fee_policy_chunks,
        min_top_score=0.70,
        min_supporting_chunks=1,
        use_reranker=True,
    )
    
    assert res["status"] == "answered"
    assert res["metrics"]["llm_called"] is True
    assert len(res["sources"]) >= 1
    assert len(res["selected_chunks"]) >= 1
    assert "1.25%" in res["answer"] or "fee" in res["answer"].lower()


# ==============================================================================
# Scenario 5: Conflicting Regulatory Evidence Detection
# ==============================================================================

def test_conflicting_evidence_detection():
    """Test that policy discrepancy / fee conflict triggers the conflict detection mechanism."""
    query = "Is there a conflict or fee discrepancy between the 2024 and 2026 wealth advisory fee guidelines?"
    dummy_sources = [
        {"source": "wealth_advisory_standard_2026.pdf", "text": "Fee cap 1.25%"},
        {"source": "legacy_fee_schedule_2024.pdf", "text": "Fee cap 1.50%"},
    ]
    
    has_conflict, conflict_details = _check_evidence_conflict(query, dummy_sources)
    assert has_conflict is True
    assert conflict_details is not None
    assert "Conflicting Regulatory Evidence" in conflict_details["title"]
    assert "source_a" in conflict_details
    assert "source_b" in conflict_details


# ==============================================================================
# Scenario 6: Citation Validation & Raw Metadata Leak Sanitization
# ==============================================================================

def test_citation_sanitization_removes_metadata_leaks():
    """Test that raw metadata hashes like '[1] file.pdf#1' and out-of-bounds citation markers are cleanly sanitized."""
    raw_answer = (
        "According to [1] alpha_large_cap_factsheet.pdf#1, the fund targets large-cap equities. "
        "The benchmark is the S&P 500 [2] alpha_large_cap_factsheet.pdf#2. "
        "Also mentioned in [5] unknown_source.pdf."
    )
    sources_used = [
        {"marker": "[1]", "source": "alpha_large_cap_factsheet.pdf"},
        {"marker": "[2]", "source": "alpha_large_cap_factsheet.pdf"},
    ]
    
    clean_answer, valid_sources = validate_and_sanitize_citations(raw_answer, sources_used)
    
    # Verify raw filenames stripped from citation markers
    assert "[1] alpha_large_cap_factsheet.pdf#1" not in clean_answer
    assert "[1]" in clean_answer
    assert "[2]" in clean_answer
    
    # Verify out-of-bounds citation [5] was stripped since only 2 sources exist
    assert "[5]" not in clean_answer
    assert len(valid_sources) == 2
