"""Tests for token-aware chunk sizing and overlap (Concept 13)."""

from pathlib import Path
import pytest
import tiktoken

from scripts.demonstrate_token_chunking import (
    compare_overlap_variations,
    compare_token_vs_char_sizing,
    demonstrate_boundary_context,
    get_model_budget_justification,
    run_demonstration,
)
from src.ingestion.chunking import (
    DEFAULT_ENCODING,
    token_chunks,
    token_chunks_with_metadata,
)


@pytest.fixture
def sample_financial_text():
    return (
        "FInee.ai is a compliance-focused financial advisory platform. "
        "Advisors must ensure that portfolio fee reductions comply strictly with SEC Rule 206(4)-1. "
        "Specifically, clients are eligible for a 0.50% advisory fee discount only if their aggregate qualifying "
        "asset balance across linked family accounts exceeds $250,000 as of the quarter-end evaluation date. "
        "Accounts failing to maintain this threshold will revert to standard asset management fee schedules without exception."
    )


def test_token_chunks_size_bounds(sample_financial_text):
    enc = tiktoken.get_encoding(DEFAULT_ENCODING)
    size = 25
    overlap = 5

    chunks_meta = token_chunks_with_metadata(
        sample_financial_text, size=size, overlap=overlap
    )
    assert len(chunks_meta) > 1

    for chunk_meta in chunks_meta:
        # Each chunk's raw token slice count must not exceed the target size
        assert chunk_meta["token_count"] <= size
        tok_count = len(enc.encode(chunk_meta["text"]))
        # Re-encoded text is within 1-2 tokens tolerance due to BPE whitespace boundary effects
        assert tok_count <= size + 2


def test_token_chunks_overlap_continuity(sample_financial_text):
    enc = tiktoken.get_encoding(DEFAULT_ENCODING)
    size = 30
    overlap = 10

    chunks_meta = token_chunks_with_metadata(
        sample_financial_text, size=size, overlap=overlap
    )
    assert len(chunks_meta) >= 2

    # Check that adjacent chunks have the expected step and overlap indices
    for i in range(len(chunks_meta) - 1):
        c1 = chunks_meta[i]
        c2 = chunks_meta[i + 1]
        expected_step = size - overlap
        assert c2["start_token_idx"] == c1["start_token_idx"] + expected_step


def test_token_chunks_zero_overlap(sample_financial_text):
    enc = tiktoken.get_encoding(DEFAULT_ENCODING)
    size = 20
    overlap = 0

    chunks = token_chunks(sample_financial_text, size=size, overlap=overlap)
    total_tokens_in_chunks = sum(len(enc.encode(c)) for c in chunks)
    original_tokens = len(enc.encode(sample_financial_text))

    # Without overlap, chunk tokens shouldn't duplicate
    assert total_tokens_in_chunks <= original_tokens + 5  # Allow minor whitespace decode variance


def test_token_chunks_empty_or_whitespace():
    assert token_chunks("") == []
    assert token_chunks("   \n\t  ") == []
    assert token_chunks_with_metadata("") == []


def test_token_chunks_short_text():
    text = "Short financial statement."
    chunks = token_chunks(text, size=100, overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_token_chunks_invalid_parameters():
    with pytest.raises(ValueError, match="Chunk size must be greater than 0"):
        token_chunks("Some text", size=0, overlap=0)

    with pytest.raises(ValueError, match="Chunk size must be greater than 0"):
        token_chunks("Some text", size=-10, overlap=0)

    with pytest.raises(ValueError, match="Overlap cannot be negative"):
        token_chunks("Some text", size=100, overlap=-5)

    with pytest.raises(ValueError, match="Overlap .* must be strictly less than chunk size"):
        token_chunks("Some text", size=50, overlap=50)

    with pytest.raises(ValueError, match="Overlap .* must be strictly less than chunk size"):
        token_chunks("Some text", size=50, overlap=60)


def test_boundary_context_preservation():
    demo = demonstrate_boundary_context()
    assert demo["no_overlap"]["intact_answer_found"] is False
    assert demo["with_overlap"]["intact_answer_found"] is True


def test_compare_overlap_variations(sample_financial_text):
    results = compare_overlap_variations(sample_financial_text, chunk_size=30, overlaps=[0, 5, 10])
    assert len(results) == 3
    # Overlap 0 has 0 duplication overhead
    assert results[0]["duplicate_token_overhead_pct"] == 0.0
    # Overlap 10 has more stored tokens than overlap 0
    assert results[2]["total_tokens_stored"] > results[0]["total_tokens_stored"]


def test_compare_token_vs_char_sizing(sample_financial_text):
    comparison = compare_token_vs_char_sizing(sample_financial_text)
    assert "character_chunking" in comparison
    assert "token_aware_chunking" in comparison
    assert comparison["token_aware_chunking"]["chunk_count"] > 0


def test_get_model_budget_justification():
    budget = get_model_budget_justification()
    assert budget["recommended_settings"]["chunk_size_tokens"] == 400
    assert budget["recommended_settings"]["overlap_tokens"] == 60
    assert budget["context_window_budget"]["headroom_remaining"] > 0


def test_run_demonstration(tmp_path):
    output_file = tmp_path / "test_eval_results.json"
    report = run_demonstration(output_path=output_file)
    assert output_file.exists()
    assert report["concept"] == "Concept 13: Token-Aware Chunk Sizing & Overlap"
    assert "task1_sizing_comparison" in report
    assert "task2_overlap_variations" in report
    assert "task3_boundary_preservation" in report
    assert "task4_model_budget_justification" in report
