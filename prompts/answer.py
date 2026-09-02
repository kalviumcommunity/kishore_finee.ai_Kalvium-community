"""Answer and RAG prompt templates for FInee.ai financial advisory platform."""

from typing import Any
from prompts.templates import PromptTemplate, render

# Standard QA prompt template as specified
ANSWER = (
    "You are a support assistant. Answer ONLY from the context.\n"
    "If the answer isn't there, say you don't know.\n\n"
    "Context:\n{context}\n\nQuestion: {question}"
)

# Financial Advisory Grounded RAG user prompt template
FINANCIAL_RAG_USER_TEMPLATE = "Context:\n{context}\n\nQuestion:\n{question}"

# Citation-grounded prompt template
CITATION_ANSWER_TEMPLATE = PromptTemplate(
    template=(
        "You are FInee.ai, a compliance-grounded financial advisory assistant.\n"
        "Answer the question strictly using the provided context. "
        "Every claim or numeric figure MUST cite the source document name.\n\n"
        "Context:\n{context}\n\n"
        "Question:\n{question}\n\n"
        "Answer with explicit citations:"
    ),
    name="citation_answer_template",
)

# Financial evaluation prompt template
EVALUATION_TEMPLATE = PromptTemplate(
    template=(
        "Evaluate whether the following generated answer is strictly grounded in the reference context.\n\n"
        "Context:\n{context}\n\n"
        "Question:\n{question}\n\n"
        "Generated Answer:\n{answer}\n\n"
        "Output format: PASS or FAIL with a 1-sentence explanation."
    ),
    name="evaluation_template",
)

__all__ = [
    "ANSWER",
    "FINANCIAL_RAG_USER_TEMPLATE",
    "CITATION_ANSWER_TEMPLATE",
    "EVALUATION_TEMPLATE",
    "render",
]
