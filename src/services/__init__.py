"""Business logic and orchestration service layer.

Connects ingestion, vector storage, retrieval, and LLM answer generation
with citation tracking and compliance verification.
"""

from .context_injection import (
    ContextInjectionError,
    TokenBudgetExceededError,
    assemble_context,
    build_prompt,
    calculate_effective_context_budget,
    count_tokens,
    format_chunk,
    format_prompt_overview,
)
from .llm import LLMConfigurationError, LLMServiceError, generate_answer, generate_grounded_answer

__all__ = [
    "generate_answer",
    "generate_grounded_answer",
    "LLMConfigurationError",
    "LLMServiceError",
    "format_chunk",
    "count_tokens",
    "assemble_context",
    "build_prompt",
    "calculate_effective_context_budget",
    "format_prompt_overview",
    "ContextInjectionError",
    "TokenBudgetExceededError",
]

