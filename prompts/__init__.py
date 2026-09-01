"""Prompts and templates package for FInee.ai."""

from prompts.templates import (
    PromptTemplate,
    PromptTemplateError,
    render,
)
from prompts.answer import (
    ANSWER,
    FINANCIAL_RAG_USER_TEMPLATE,
    CITATION_ANSWER_TEMPLATE,
    EVALUATION_TEMPLATE,
)
from prompts.system import (
    COMPLIANCE_SYSTEM_PROMPT,
    CONVERSATIONAL_SYSTEM_PROMPT,
    FINANCIAL_INFO_SYSTEM_PROMPT,
    STRUCTURED_OUTPUT_SYSTEM_PROMPT,
    GUARDRAIL_SYSTEM_TEMPLATE,
)

__all__ = [
    "PromptTemplate",
    "PromptTemplateError",
    "render",
    "ANSWER",
    "FINANCIAL_RAG_USER_TEMPLATE",
    "CITATION_ANSWER_TEMPLATE",
    "EVALUATION_TEMPLATE",
    "COMPLIANCE_SYSTEM_PROMPT",
    "CONVERSATIONAL_SYSTEM_PROMPT",
    "FINANCIAL_INFO_SYSTEM_PROMPT",
    "STRUCTURED_OUTPUT_SYSTEM_PROMPT",
    "GUARDRAIL_SYSTEM_TEMPLATE",
]
