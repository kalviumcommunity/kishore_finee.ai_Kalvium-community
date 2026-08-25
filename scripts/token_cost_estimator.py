"""Estimate token usage and model-call cost for two text files."""

import argparse
import json
from pathlib import Path

from src.services.token_usage import estimate_cost


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", type=Path, help="File containing model input")
    parser.add_argument("answer", type=Path, help="File containing expected model output")
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--input-price", type=float, default=0.0005)
    parser.add_argument("--output-price", type=float, default=0.0015)
    return parser


def main() -> None:
    """Read files and print a machine-readable cost estimate."""
    args = build_parser().parse_args()
    estimate = estimate_cost(
        args.prompt.read_text(encoding="utf-8"),
        args.answer.read_text(encoding="utf-8"),
        encoding_name=args.encoding,
        input_price_per_1k=args.input_price,
        output_price_per_1k=args.output_price,
    )
    print(
        json.dumps(
            {
                "input_tokens": estimate.input_tokens,
                "output_tokens": estimate.output_tokens,
                "input_cost": round(estimate.input_cost, 6),
                "output_cost": round(estimate.output_cost, 6),
                "total_cost": round(estimate.total_cost, 6),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()