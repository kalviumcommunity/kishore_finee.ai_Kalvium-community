"""Business logic and orchestration service layer.

Connects ingestion, vector storage, retrieval, and LLM answer generation
with citation tracking and compliance verification.
"""

from .llm import generate_answer, LLMConfigurationError, LLMServiceError

__all__ = ["generate_answer", "LLMConfigurationError", "LLMServiceError"]
