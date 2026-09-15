"""Demonstration script for Context Injection and Prompt Augmentation in finee.ai.

Demonstrates:
1. Formatting retrieved chunks with standardized citation markers ([1] doc.pdf#12).
2. Token counting and dynamic model budget calculation.
3. Assembling context within strict token budgets (stopping before limit, skipping oversized chunks).
4. Constructing augmented prompts with distinct System, Context, and Question sections.
5. Preserving chunk provenance metadata for downstream citation generation.
6. Exporting structured prompt and evaluation payloads to outputs/evaluations/.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.services.context_injection import (
    assemble_context,
    build_prompt,
    calculate_effective_context_budget,
    count_tokens,
    format_chunk,
    format_prompt_overview,
)

OUTPUT_DIR = Path("outputs/evaluations")
OUTPUT_FILE = OUTPUT_DIR / "context_injection_results.json"

SAMPLE_RETRIEVED_CHUNKS = [
    {
        "rank": 1,
        "score": 0.9420,
        "text": "Client Advisory Billing Evidence: Advisory fee of $1,250.00 for Q3 wealth advisory services was charged to Marcus on 20 August 2026, confirmed via invoice #INV-2026-08.",
        "metadata": {
            "source": "client-billing-records.pdf",
            "document_id": "doc_billing_01",
            "chunk_index": 1,
            "section": "Invoice Verification",
            "approval_status": "approved",
        },
        "id": "doc_billing_01:1",
    },
    {
        "rank": 2,
        "score": 0.9150,
        "text": "Standard Fee Schedule: The annual advisory fee is 0.75% of assets under management, calculated and deducted on a quarterly basis in arrears.",
        "metadata": {
            "source": "fee-schedule.pdf",
            "document_id": "doc_fee_01",
            "chunk_index": 0,
            "section": "Fee Terms",
            "approval_status": "approved",
        },
        "id": "doc_fee_01:0",
    },
    {
        "rank": 3,
        "score": 0.8840,
        "text": "Advisory Agreement Terms: Clients agree to electronic fee deduction upon quarterly statement issuance with 14 days notice for dispute submission.",
        "metadata": {
            "source": "advisory-agreement.md",
            "document_id": "doc_agreement_01",
            # chunk_index intentionally omitted to test graceful fallback
            "section": "Dispute Terms",
            "approval_status": "approved",
        },
        "id": "doc_agreement_01:terms",
    },
    {
        "rank": 4,
        "score": 0.8120,
        "text": "Client Portal Access: Clients can download official PDF receipts and historical fee summaries from the documents tab.",
        "metadata": {
            "source": "client-portal.md",
            "document_id": "doc_portal_01",
            "chunk_index": 3,
            "section": "Portal Usage",
            "approval_status": "approved",
        },
        "id": "doc_portal_01:3",
    },
]


def run_demonstration() -> Dict[str, Any]:
    """Execute context injection demonstration and return evaluation results."""
    print("=" * 70)
    print("FInee.ai - CONTEXT INJECTION & PROMPT AUGMENTATION DEMONSTRATION")
    print("=" * 70)

    # 1. Budget Configuration Overview
    max_model_tokens = settings.MAX_MODEL_CONTEXT_TOKENS
    max_context_tokens = settings.MAX_CONTEXT_TOKENS
    reserved_ans = settings.RESERVED_ANSWER_TOKENS
    reserved_inst = settings.RESERVED_INSTRUCTION_TOKENS
    effective_budget = calculate_effective_context_budget()

    print("\n1. Token Budget Allocation:")
    print("-" * 50)
    print(f"  Total Model Context Window : {max_model_tokens} tokens")
    print(f"  Reserved for Answer Output : {reserved_ans} tokens")
    print(f"  Reserved for Instructions  : {reserved_inst} tokens")
    print(f"  Configured Max Context     : {max_context_tokens} tokens")
    print(f"  Effective Context Budget   : {effective_budget} tokens")

    # 2. Chunk Source-Marker Formatting
    print("\n2. Chunk Formatting & Source Markers:")
    print("-" * 50)
    for idx, chunk in enumerate(SAMPLE_RETRIEVED_CHUNKS, start=1):
        formatted = format_chunk(idx, chunk)
        tokens = count_tokens(formatted)
        print(f"--- Chunk {idx} (Tokens: {tokens}) ---")
        print(formatted)
        print()

    # 3. Context Assembly with Standard vs Constrained Budgets
    print("3. Context Assembly under Different Budgets:")
    print("-" * 50)
    standard_assembly = assemble_context(SAMPLE_RETRIEVED_CHUNKS, max_context_tokens=5000)
    print(f"Standard Budget (5000 tokens): Selected {len(standard_assembly['selected_chunks'])} / {len(SAMPLE_RETRIEVED_CHUNKS)} chunks ({standard_assembly['context_tokens']} tokens)")
    print(f"Source Markers: {', '.join(standard_assembly['source_markers'])}")

    # Constrained budget: only fits ~1 chunk
    constrained_assembly = assemble_context(SAMPLE_RETRIEVED_CHUNKS, max_context_tokens=45)
    print(f"Constrained Budget (45 tokens): Selected {len(constrained_assembly['selected_chunks'])} / {len(SAMPLE_RETRIEVED_CHUNKS)} chunks ({constrained_assembly['context_tokens']} tokens)")
    print(f"Source Markers: {', '.join(constrained_assembly['source_markers'])}")

    # 4. Prompt Augmentation with Grounded Compliance Rules
    question = "What evidence supports the advisory fee charged to Marcus and what is the fee rate?"
    prompt_info = build_prompt(
        question=question,
        retrieved_chunks=SAMPLE_RETRIEVED_CHUNKS,
        max_context_tokens=5000,
    )

    print("\n4. Augmented Prompt Structure:")
    print("-" * 50)
    print(prompt_info["prompt"])

    # 5. Formatted Overview Report
    print("\n5. Structured Prompt Overview:")
    print("-" * 50)
    overview_text = format_prompt_overview(prompt_info)
    print(overview_text)

    # 6. Fallback Behavior on Empty Context
    empty_prompt_info = build_prompt(
        question="What is the penalty for early withdrawal from the fixed deposit?",
        retrieved_chunks=[],
    )
    print("\n6. Fallback Prompt (No Context Retrieved):")
    print("-" * 50)
    print(empty_prompt_info["user_prompt"])

    # Save demonstration results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_payload = {
        "budget_allocation": {
            "max_model_tokens": max_model_tokens,
            "reserved_answer_tokens": reserved_ans,
            "reserved_instruction_tokens": reserved_inst,
            "max_context_tokens": max_context_tokens,
            "effective_budget": effective_budget,
        },
        "query_demonstration": {
            "question": question,
            "context_tokens": prompt_info["context_tokens"],
            "source_markers": prompt_info["source_markers"],
            "sources_used": prompt_info["sources_used"],
            "selected_chunks_count": len(prompt_info["selected_chunks"]),
            "augmented_prompt_sample": prompt_info["prompt"],
        },
        "budget_enforcement_demonstration": {
            "standard_selected_count": len(standard_assembly["selected_chunks"]),
            "standard_tokens": standard_assembly["context_tokens"],
            "constrained_selected_count": len(constrained_assembly["selected_chunks"]),
            "constrained_tokens": constrained_assembly["context_tokens"],
        },
        "empty_context_fallback": {
            "question": empty_prompt_info["question"],
            "context_tokens": empty_prompt_info["context_tokens"],
            "selected_chunks_count": len(empty_prompt_info["selected_chunks"]),
            "user_prompt": empty_prompt_info["user_prompt"],
        },
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print(f"\nSaved demonstration results to: {OUTPUT_FILE}")
    return results_payload


if __name__ == "__main__":
    run_demonstration()
