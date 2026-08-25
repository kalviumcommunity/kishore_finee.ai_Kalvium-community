"""Tests for the three-sample token-counting demonstration."""

from scripts.token_count_demo import build_samples, create_report


def test_demo_contains_three_varying_samples():
    samples = build_samples()
    report = create_report()

    assert len(samples) == 3
    assert len(report) == 3
    assert report[0]["input_tokens"] < report[1]["input_tokens"] < report[2]["input_tokens"]


def test_demo_reports_length_and_separate_costs():
    result = create_report()[0]

    assert result["input_characters"] > 0
    assert result["input_words"] > 0
    assert result["input_tokens"] > 0
    assert result["output_tokens"] > 0
    assert result["input_cost"] != result["output_cost"]
    assert result["total_cost"] == result["input_cost"] + result["output_cost"]