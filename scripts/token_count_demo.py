"""Print token counts, length comparisons, and cost estimates for three samples."""

import argparse
import json
from pathlib import Path

from src.services.token_usage import count_tokens, estimate_cost


INPUT_PRICE_PER_1K = 0.0005
OUTPUT_PRICE_PER_1K = 0.0015


def build_samples() -> list[dict[str, str]]:
    """Build three samples from short, paragraph, and project-document text."""
    project_root = Path(__file__).resolve().parents[1]
    project_document = (project_root / "README.md").read_text(encoding="utf-8")
    return [
        {
            "name": "short question",
            "input": "What is our refund window?",
            "output": "The refund window is 30 days.",
        },
        {
            "name": "financial paragraph",
            "input": (
                "A compliance-grounded assistant retrieves approved financial research "
                "before answering an advisor's question. It should cite the source, "
                "respect document permissions, and avoid unsupported recommendations."
            ),
            "output": (
                "The assistant should answer only from approved evidence and include "
                "an exact citation so the advisor can verify the response."
            ),
        },
        {
            "name": "full project document",
            "input": project_document,
            "output": (
                "The project is a compliance-grounded financial RAG platform with "
                "ingestion, embeddings, retrieval, and cited answer generation."
            ),
        },
    ]


def create_report() -> list[dict[str, object]]:
    """Return token and cost measurements for all demonstration samples."""
    report = []
    for sample in build_samples():
        input_text = sample["input"]
        output_text = sample["output"]
        estimate = estimate_cost(
            input_text,
            output_text,
            input_price_per_1k=INPUT_PRICE_PER_1K,
            output_price_per_1k=OUTPUT_PRICE_PER_1K,
        )
        report.append(
            {
                "sample": sample["name"],
                "input_characters": len(input_text),
                "input_words": len(input_text.split()),
                "input_tokens": estimate.input_tokens,
                "output_characters": len(output_text),
                "output_words": len(output_text.split()),
                "output_tokens": estimate.output_tokens,
                "input_cost": round(estimate.input_cost, 6),
                "output_cost": round(estimate.output_cost, 6),
                "total_cost": round(estimate.total_cost, 6),
            }
        )
    return report


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for saving the JSON report",
    )
    return parser


def main() -> None:
    """Print the demonstration report and optionally save it."""
    args = build_parser().parse_args()
    report = json.dumps(create_report(), indent=2)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()