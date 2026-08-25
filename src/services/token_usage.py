"""Token counting and cost estimation utilities."""

from dataclasses import dataclass
from typing import Iterable

import tiktoken


DEFAULT_ENCODING = "cl100k_base"
DEFAULT_INPUT_PRICE_PER_1K = 0.0005
DEFAULT_OUTPUT_PRICE_PER_1K = 0.0015


@dataclass(frozen=True)
class CostEstimate:
    """Token usage and estimated cost for one model call."""

    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float

    @property
    def total_cost(self) -> float:
        """Return the combined estimated input and output cost."""
        return self.input_cost + self.output_cost


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """Count tokens using the requested tiktoken encoding."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def count_documents(
    documents: Iterable[str], encoding_name: str = DEFAULT_ENCODING
) -> int:
    """Return the total token count across a collection of documents."""
    encoding = tiktoken.get_encoding(encoding_name)
    return sum(len(encoding.encode(document)) for document in documents)


def estimate_cost_from_tokens(
    input_tokens: int,
    output_tokens: int,
    input_price_per_1k: float = DEFAULT_INPUT_PRICE_PER_1K,
    output_price_per_1k: float = DEFAULT_OUTPUT_PRICE_PER_1K,
) -> CostEstimate:
    """Estimate cost from token counts and provider prices per 1,000 tokens."""
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts cannot be negative")
    if input_price_per_1k < 0 or output_price_per_1k < 0:
        raise ValueError("Token prices cannot be negative")

    input_cost = input_tokens / 1_000 * input_price_per_1k
    output_cost = output_tokens / 1_000 * output_price_per_1k
    return CostEstimate(input_tokens, output_tokens, input_cost, output_cost)


def estimate_cost(
    prompt: str,
    answer: str,
    encoding_name: str = DEFAULT_ENCODING,
    input_price_per_1k: float = DEFAULT_INPUT_PRICE_PER_1K,
    output_price_per_1k: float = DEFAULT_OUTPUT_PRICE_PER_1K,
) -> CostEstimate:
    """Count prompt and answer tokens, then estimate the model call cost."""
    return estimate_cost_from_tokens(
        count_tokens(prompt, encoding_name),
        count_tokens(answer, encoding_name),
        input_price_per_1k,
        output_price_per_1k,
    )