"""Unit tests for prompt templates, rendering engine, and reusable prompt design."""

import pytest
from prompts.answer import (
    ANSWER,
    CITATION_ANSWER_TEMPLATE,
    EVALUATION_TEMPLATE,
    FINANCIAL_RAG_USER_TEMPLATE,
    render,
)
from prompts.system import (
    COMPLIANCE_SYSTEM_PROMPT,
    CONVERSATIONAL_SYSTEM_PROMPT,
    FINANCIAL_INFO_SYSTEM_PROMPT,
    GUARDRAIL_SYSTEM_TEMPLATE,
    STRUCTURED_OUTPUT_SYSTEM_PROMPT,
)
from prompts.templates import PromptTemplate, PromptTemplateError


def test_answer_template_structure():
    """Verify that ANSWER template contains required placeholders and grounding rules."""
    assert "{context}" in ANSWER
    assert "{question}" in ANSWER
    assert "support assistant" in ANSWER
    assert "Answer ONLY from the context" in ANSWER


def test_render_string_template_success():
    """Verify render function successfully substitutes placeholders in string templates."""
    context_text = "Fund Alpha returned 10% in 2025."
    question_text = "What was the return of Fund Alpha?"
    
    result = render(ANSWER, context=context_text, question=question_text)
    
    assert "Context:\nFund Alpha returned 10% in 2025." in result
    assert "Question: What was the return of Fund Alpha?" in result
    assert "{context}" not in result
    assert "{question}" not in result


def test_render_string_template_missing_variable():
    """Verify render raises PromptTemplateError when required placeholders are missing."""
    with pytest.raises(PromptTemplateError) as excinfo:
        render(ANSWER, context="Some context")
    assert "question" in str(excinfo.value)


def test_render_prompt_template_object():
    """Verify PromptTemplate class renders correctly."""
    custom = PromptTemplate(
        template="Hello {name}, your account balance is {balance}.",
        name="balance_notice",
    )
    assert custom.name == "balance_notice"
    assert custom.input_variables == {"name", "balance"}
    
    output = custom.render(name="Alice", balance="$5,000")
    assert output == "Hello Alice, your account balance is $5,000."
    
    # Test __call__ interface
    output_call = custom(name="Bob", balance="$10,000")
    assert output_call == "Hello Bob, your account balance is $10,000."


def test_prompt_template_missing_variable_error():
    """Verify PromptTemplate raises PromptTemplateError on missing inputs."""
    custom = PromptTemplate(
        template="Context: {context}, Query: {query}, Role: {role}",
        name="test_template",
    )
    with pytest.raises(PromptTemplateError) as excinfo:
        custom.render(context="data")
    assert "query" in str(excinfo.value)
    assert "role" in str(excinfo.value)


def test_prompt_template_invalid_type():
    """Verify PromptTemplate raises PromptTemplateError when non-string is passed."""
    with pytest.raises(PromptTemplateError):
        PromptTemplate(123)  # type: ignore


def test_render_invalid_template_type():
    """Verify render function raises PromptTemplateError for invalid template type."""
    with pytest.raises(PromptTemplateError):
        render(12345, key="val")  # type: ignore


def test_citation_answer_template():
    """Verify CITATION_ANSWER_TEMPLATE enforces citations and renders correctly."""
    assert isinstance(CITATION_ANSWER_TEMPLATE, PromptTemplate)
    rendered = CITATION_ANSWER_TEMPLATE.render(
        context="AUM is $1.2B as per 2025 Annual Report.",
        question="What is the AUM?",
    )
    assert "citations" in rendered.lower()
    assert "AUM is $1.2B as per 2025 Annual Report." in rendered
    assert "What is the AUM?" in rendered


def test_evaluation_template():
    """Verify EVALUATION_TEMPLATE renders context, question, and answer."""
    assert isinstance(EVALUATION_TEMPLATE, PromptTemplate)
    rendered = EVALUATION_TEMPLATE.render(
        context="Sample context",
        question="Sample question",
        answer="Sample answer",
    )
    assert "PASS or FAIL" in rendered
    assert "Sample context" in rendered
    assert "Sample question" in rendered
    assert "Sample answer" in rendered


def test_guardrail_system_template():
    """Verify GUARDRAIL_SYSTEM_TEMPLATE dynamic parameter injection."""
    assert isinstance(GUARDRAIL_SYSTEM_TEMPLATE, PromptTemplate)
    rendered = GUARDRAIL_SYSTEM_TEMPLATE.render(
        compliance_level="Level 1",
        fallback_message="Unknown",
        prohibited_topics="Stock tips",
    )
    assert "Strict compliance mode: Level 1" in rendered
    assert "Stock tips" in rendered


def test_system_prompt_constants():
    """Verify all system prompt constants are non-empty strings with expected keywords."""
    assert "grounding rules" in COMPLIANCE_SYSTEM_PROMPT.lower()
    assert "financial advisory" in COMPLIANCE_SYSTEM_PROMPT.lower()
    assert "concise" in CONVERSATIONAL_SYSTEM_PROMPT.lower()
    assert "financial information assistant" in FINANCIAL_INFO_SYSTEM_PROMPT.lower()
    assert "JSON object" in STRUCTURED_OUTPUT_SYSTEM_PROMPT
