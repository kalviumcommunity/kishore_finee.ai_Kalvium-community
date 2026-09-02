#!/usr/bin/env python3
"""Demonstration script showcasing reusable prompt templates in FInee.ai.

Demonstrates:
1. Defining prompt templates with named placeholders ({context}, {question}, etc.).
2. Injecting dynamic values at runtime using render().
3. Reusing the same template across multiple features (Chat, Batch Evaluation, CLI).
4. Keeping prompts cleanly separated from business logic.
"""

import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# pyrefly: ignore [missing-import]
from prompts.answer import ANSWER, CITATION_ANSWER_TEMPLATE, FINANCIAL_RAG_USER_TEMPLATE  # type: ignore
# pyrefly: ignore [missing-import]
from prompts.system import COMPLIANCE_SYSTEM_PROMPT, GUARDRAIL_SYSTEM_TEMPLATE  # type: ignore
# pyrefly: ignore [missing-import]
from prompts.templates import PromptTemplate, PromptTemplateError, render  # type: ignore



def demo_basic_template_rendering():
    """Demonstrate basic prompt template rendering with named placeholders."""
    print("=" * 70)
    print("1. BASIC TEMPLATE RENDERING")
    print("=" * 70)

    sample_context = (
        "Apex Horizon Fund (Class A):\n"
        "- Inception: 2020\n"
        "- 3-Year Annualized Return: 9.85%\n"
        "- Risk Category: Moderate\n"
        "- Fund Manager: Marcus Vance"
    )
    sample_question = "What is the 3-year annualized return of Apex Horizon Fund?"

    # Render standard ANSWER template
    rendered_prompt = render(ANSWER, context=sample_context, question=sample_question)

    print("\n[Template Source (prompts/answer.py)]:")
    print(ANSWER)
    print("\n[Rendered Prompt at Runtime]:")
    print(rendered_prompt)
    print("-" * 70)


def demo_one_template_multiple_features():
    """Demonstrate reusing the same template across multiple features."""
    print("\n" + "=" * 70)
    print("2. ONE TEMPLATE ACROSS MULTIPLE FEATURES")
    print("=" * 70)

    context = "Q4 Financial Disclosure: Total revenue grew by 14.2% YoY to $4.8B."
    
    # Feature 1: Interactive Chat
    user_query_1 = "How much did revenue grow in Q4?"
    chat_message = render(ANSWER, context=context, question=user_query_1)
    print(f"\n[Feature 1: Interactive Chat Endpoint]\n{chat_message}\n")

    # Feature 2: Batch Evaluator
    batch_questions = [
        "What was the total revenue?",
        "What was the YoY growth rate?",
    ]
    print("[Feature 2: Batch Evaluator Pipeline]")
    for i, q in enumerate(batch_questions, 1):
        batch_prompt = render(ANSWER, context=context, question=q)
        print(f"  Batch Item #{i} prompt rendered (length: {len(batch_prompt)} chars)")

    # Feature 3: CLI Query Tool
    cli_query = "Summarize the Q4 financial performance."
    cli_prompt = render(ANSWER, context=context, question=cli_query)
    print(f"\n[Feature 3: Terminal CLI Utility]\n{cli_prompt}\n")


def demo_advanced_prompt_template_object():
    """Demonstrate PromptTemplate class with validation and custom variables."""
    print("=" * 70)
    print("3. PROMPT TEMPLATE OBJECT & ERROR HANDLING")
    print("=" * 70)

    # Define a custom template
    portfolio_template = PromptTemplate(
        template=(
            "Client Profile: {client_name} (Risk Tolerance: {risk_tolerance})\n"
            "Approved Portfolio Models:\n{approved_models}\n\n"
            "Inquiry: {inquiry}\n\n"
            "Provide suitable allocation options strictly from approved models."
        ),
        name="portfolio_allocation_template",
    )

    print(f"\nTemplate Name: {portfolio_template.name}")
    print(f"Required Variables: {sorted(portfolio_template.input_variables)}")

    # Successful render
    rendered = portfolio_template.render(
        client_name="Eleanor Vance",
        risk_tolerance="Moderate-Conservative",
        approved_models="1. Conservative Income Fund\n2. Balanced Growth Portfolio",
        inquiry="What allocation model suits my retirement horizon of 7 years?",
    )
    print("\n[Successfully Rendered Portfolio Template]:")
    print(rendered)

    # Missing variable validation demonstration
    print("\n[Validation Check: Handling Missing Placeholders]:")
    try:
        portfolio_template.render(
            client_name="Eleanor Vance",
            risk_tolerance="Moderate-Conservative",
            # missing 'approved_models' and 'inquiry'
        )
    except PromptTemplateError as err:
        print(f"Caught expected error:\n  -> {err}")


def demo_citation_and_compliance_templates():
    """Demonstrate citation enforcement and compliance guardrails."""
    print("\n" + "=" * 70)
    print("4. CITATION ENFORCEMENT & COMPLIANCE GUARDRAIL TEMPLATES")
    print("=" * 70)

    doc_context = (
        "[Document: SEC Form 10-K, 2025]\n"
        "Operating margin increased to 28.5% compared to 24.1% in 2024."
    )
    question = "What was the operating margin in 2025?"

    citation_prompt = render(
        CITATION_ANSWER_TEMPLATE,
        context=doc_context,
        question=question,
    )
    print("[Citation Prompt Template Output]:")
    print(citation_prompt)

    guardrail_prompt = render(
        GUARDRAIL_SYSTEM_TEMPLATE,
        compliance_level="Level 3 (Strict Financial Regulatory Adherence)",
        fallback_message="Information not available in verified compliance documents.",
        prohibited_topics="Price speculation, tax advice, crypto trading",
    )
    print("\n[Guardrail System Template Output]:")
    print(guardrail_prompt)


def main():
    print("######################################################################")
    print("      FInee.ai - Prompt Templates & Reusable Prompt Design Demo       ")
    print("######################################################################\n")
    demo_basic_template_rendering()
    demo_one_template_multiple_features()
    demo_advanced_prompt_template_object()
    demo_citation_and_compliance_templates()
    print("\n######################################################################")
    print("                 Demonstration Completed Successfully                ")
    print("######################################################################")


if __name__ == "__main__":
    main()
