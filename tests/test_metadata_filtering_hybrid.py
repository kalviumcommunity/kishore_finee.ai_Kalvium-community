"""Unit and integration test suite for Metadata Filtering & Hybrid Search in finee.ai."""

from __future__ import annotations

from typing import Any, Dict, List
import pytest

from src.embeddings.embedding_service import EmbeddingService, get_embedding_service
from src.retrieval.chroma_store import ChromaVectorStore
from src.retrieval.retriever import (
    compare_filtered_unfiltered,
    hybrid_rank,
    hybrid_retrieve,
    keyword_score,
    retrieve,
    show_results,
)
from src.retrieval.vector_store import InMemoryVectorStore


@pytest.fixture
def test_corpus() -> List[Dict[str, Any]]:
    """Fixture providing structured multi-domain financial and compliance chunks."""
    return [
        {
            "text": "To reset your password, visit the login portal and click 'Forgot Password' for an OTP.",
            "metadata": {
                "source": "auth_guide.md",
                "section": "Account access",
                "category": "security",
                "document_id": "doc_001",
                "user_role": "client",
            },
        },
        {
            "text": "Enterprise IT staff must rotate database root passwords every 90 days as per security policy.",
            "metadata": {
                "source": "it_policy.pdf",
                "section": "Infrastructure Security",
                "category": "internal_it",
                "document_id": "doc_002",
                "user_role": "admin",
            },
        },
        {
            "text": "Under Section 80C, maximum deduction allowed is Rs 1,50,000 across PPF, ELSS, and insurance.",
            "metadata": {
                "source": "tax_guide.pdf",
                "section": "Section 80C Deductions",
                "category": "taxation",
                "document_id": "doc_003",
                "user_role": "taxpayer",
            },
        },
        {
            "text": "Section 54 provides capital gains tax exemption when proceeds are invested in a residential house.",
            "metadata": {
                "source": "tax_guide.pdf",
                "section": "Capital Gains Exemption",
                "category": "taxation",
                "document_id": "doc_004",
                "user_role": "taxpayer",
            },
        },
        {
            "text": "SEBI circular SEBI-CIR-2026-42 mandates Aadhaar-based digital e-KYC and V-CIP for onboarding.",
            "metadata": {
                "source": "sebi_circular.pdf",
                "section": "KYC Guidelines",
                "category": "compliance",
                "compliance_code": "SEBI-CIR-2026-42",
                "document_id": "doc_005",
                "user_role": "compliance_officer",
            },
        },
    ]


@pytest.fixture
def populated_store(test_corpus: List[Dict[str, Any]]) -> InMemoryVectorStore:
    """Fixture providing an InMemoryVectorStore loaded with test corpus."""
    store = InMemoryVectorStore(name="test_store")
    store.add_chunks(test_corpus)
    return store


# =============================================================================
# Task 1 Tests: Metadata Filtering
# =============================================================================

def test_metadata_filter_section(populated_store: InMemoryVectorStore):
    """Test filtering vector search to a single section."""
    results = retrieve(
        query="What are the password reset steps?",
        k=5,
        collection=populated_store,
        metadata_filter={"section": "Account access"},
    )
    assert len(results) == 1
    assert results[0]["metadata"]["section"] == "Account access"
    assert "Forgot Password" in results[0]["text"]


def test_metadata_filter_multiple_fields(populated_store: InMemoryVectorStore):
    """Test filtering vector search on multiple metadata key-value constraints."""
    results = retrieve(
        query="tax deductions",
        k=5,
        collection=populated_store,
        filter_metadata={"category": "taxation", "section": "Section 80C Deductions"},
    )
    assert len(results) == 1
    assert results[0]["metadata"]["category"] == "taxation"
    assert results[0]["metadata"]["section"] == "Section 80C Deductions"
    assert "Section 80C" in results[0]["text"]


def test_metadata_filter_no_match(populated_store: InMemoryVectorStore):
    """Test filter that matches zero documents returns an empty list."""
    results = retrieve(
        query="password",
        k=3,
        collection=populated_store,
        metadata_filter={"section": "NonExistentSection"},
    )
    assert results == []


# =============================================================================
# Task 2 & 4 Tests: Filtered vs Unfiltered Precision Comparison
# =============================================================================

def test_compare_filtered_unfiltered(populated_store: InMemoryVectorStore):
    """Test comparing unfiltered vs filtered retrieval for precision improvements."""
    comparison = compare_filtered_unfiltered(
        query="What are the password reset steps?",
        filter_metadata={"section": "Account access"},
        keywords=["password", "reset", "otp"],
        k=3,
        collection=populated_store,
    )

    assert "unfiltered_results" in comparison
    assert "filtered_results" in comparison
    assert "hybrid_results" in comparison
    assert len(comparison["filtered_results"]) <= len(comparison["unfiltered_results"])

    # Ensure all filtered results respect the section filter
    for item in comparison["filtered_results"]:
        assert item["metadata"]["section"] == "Account access"

    metrics = comparison["metrics"]
    assert metrics["filtered_count"] == 1
    assert metrics["top_filtered_section"] == "Account access"


def test_precision_improvement_eliminates_distractors(populated_store: InMemoryVectorStore):
    """Verify that filtering excludes out-of-scope enterprise IT policies for retail password query."""
    unfiltered = retrieve(
        query="password policy",
        k=5,
        collection=populated_store,
        filter_metadata=None,
    )
    filtered = retrieve(
        query="password policy",
        k=5,
        collection=populated_store,
        filter_metadata={"category": "security", "user_role": "client"},
    )

    unfiltered_sources = [r["metadata"]["source"] for r in unfiltered]
    filtered_sources = [r["metadata"]["source"] for r in filtered]

    assert len(filtered) == 1
    assert "it_policy.pdf" not in filtered_sources
    assert filtered_sources == ["auth_guide.md"]


# =============================================================================
# Task 3 Tests: Keyword Matching & Hybrid Ranking
# =============================================================================

def test_keyword_score_basic():
    """Test keyword_score counts matches case-insensitively."""
    text = "SEBI circular SEBI-CIR-2026-42 mandates digital Aadhaar e-KYC and V-CIP verification."
    score_all = keyword_score(text, ["sebi-cir-2026-42", "aadhaar", "e-kyc", "v-cip"])
    assert score_all == 4

    score_partial = keyword_score(text, ["aadhaar", "passport", "pan"])
    assert score_partial == 1

    score_none = keyword_score(text, ["bitcoin", "crypto"])
    assert score_none == 0

    assert keyword_score("", ["keyword"]) == 0
    assert keyword_score("text", []) == 0


def test_hybrid_rank_weighting():
    """Test hybrid_rank combines vector score and keyword score with given weights."""
    mock_results = [
        {"id": "1", "score": 0.90, "text": "General financial planning handbook advice."},
        {"id": "2", "score": 0.70, "text": "Under Section 80C ELSS mutual funds qualify for tax deduction."},
    ]
    keywords = ["80c", "elss", "deduction"]

    # Hybrid ranking with 0.8 vector weight and 0.2 keyword weight
    # item 1: (0.8 * 0.90) + (0.2 * 0) = 0.72
    # item 2: (0.8 * 0.70) + (0.2 * 3) = 0.56 + 0.60 = 1.16
    hybrid = hybrid_rank(mock_results, keywords=keywords, vector_weight=0.8, keyword_weight=0.2)

    assert len(hybrid) == 2
    assert hybrid[0]["id"] == "2"  # Item 2 boosted to rank 1 due to keyword hits
    assert hybrid[0]["rank"] == 1
    assert hybrid[0]["keyword_score"] == 3
    assert hybrid[0]["hybrid_score"] == 1.16
    assert hybrid[1]["id"] == "1"
    assert hybrid[1]["rank"] == 2
    assert hybrid[1]["keyword_score"] == 0
    assert hybrid[1]["hybrid_score"] == 0.72


def test_hybrid_retrieve_end_to_end(populated_store: InMemoryVectorStore):
    """Test hybrid_retrieve executes vector search, filtering, and keyword reranking in one step."""
    results = hybrid_retrieve(
        query="What are the client onboarding rules under SEBI-CIR-2026-42?",
        keywords=["sebi-cir-2026-42", "e-kyc", "aadhaar"],
        k=3,
        collection=populated_store,
        filter_metadata={"category": "compliance"},
        vector_weight=0.7,
        keyword_weight=0.3,
    )
    assert len(results) == 1
    assert results[0]["metadata"]["compliance_code"] == "SEBI-CIR-2026-42"
    assert results[0]["keyword_score"] >= 2
    assert "hybrid_score" in results[0]


def test_show_results_formatting(capsys):
    """Test show_results utility prints required fields without error."""
    sample_results = [
        {
            "score": 0.8521,
            "hybrid_score": 1.2521,
            "keyword_score": 2,
            "metadata": {"source": "test_guide.pdf", "section": "Security"},
            "text": "Sample text for testing output format.",
        }
    ]
    show_results("test header", sample_results)
    captured = capsys.readouterr().out
    assert "TEST HEADER" in captured
    assert "0.8521" in captured
    assert "1.2521" in captured
    assert "test_guide.pdf" in captured
    assert "Security" in captured


# =============================================================================
# ChromaVectorStore Integration Tests
# =============================================================================

def test_chroma_store_metadata_filtering(tmp_path, test_corpus: List[Dict[str, Any]]):
    """Test metadata filtering against ChromaVectorStore."""
    chroma = ChromaVectorStore(
        collection_name="test_chroma_filtered",
        persist_directory=str(tmp_path / "chroma_db"),
    )
    chroma.add_chunks(test_corpus)

    results = retrieve(
        query="tax deductions",
        k=5,
        collection=chroma,
        metadata_filter={"category": "taxation", "section": "Section 80C Deductions"},
    )
    assert len(results) == 1
    assert results[0]["metadata"]["section"] == "Section 80C Deductions"
    assert "Section 80C" in results[0]["text"]
