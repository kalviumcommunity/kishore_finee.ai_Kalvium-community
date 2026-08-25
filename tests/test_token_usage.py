"""Tests for token counting and cost estimation."""

import pytest

from src.services.token_usage import (
    count_documents,
    count_tokens,
    estimate_cost,
    estimate_cost_from_tokens,
)


def test_count_tokens_is_deterministic():
    text = "What is our refund window?"

    assert count_tokens(text) == count_tokens(text)
    assert count_tokens("") == 0


def test_count_documents_sums_each_document():
    documents = ["refund", "window"]

    assert count_documents(documents) == count_tokens("refund") + count_tokens("window")


def test_estimate_cost_uses_separate_input_and_output_prices():
    estimate = estimate_cost_from_tokens(2_000, 1_000, 0.50, 1.50)

    assert estimate.input_cost == pytest.approx(1.00)
    assert estimate.output_cost == pytest.approx(1.50)
    assert estimate.total_cost == pytest.approx(2.50)


def test_estimate_cost_counts_prompt_and_answer():
    estimate = estimate_cost("refund", "The refund window is 30 days.")

    assert estimate.input_tokens == count_tokens("refund")
    assert estimate.output_tokens == count_tokens("The refund window is 30 days.")


@pytest.mark.parametrize("input_tokens, output_tokens", [(-1, 0), (0, -1)])
def test_negative_token_counts_are_rejected(input_tokens: int, output_tokens: int):
    with pytest.raises(ValueError, match="cannot be negative"):
        estimate_cost_from_tokens(input_tokens, output_tokens)