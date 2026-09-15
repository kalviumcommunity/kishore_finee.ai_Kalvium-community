"""Demonstration script for Retrieval Guardrails and Safe Refusal in finee.ai.

Demonstrates:
1. Retrieval strength validation (MIN_TOP_SCORE=0.72, MIN_SUPPORTING_CHUNKS=1).
2. Refusal reasons: answered, refused_weak_context, refused_empty_context, refused_insufficient_support.
3. Pre-LLM refusal preventing unsupported generation and hallucination.
4. Preserving citations and context injection when retrieval is strong.
5. Exporting evaluation diagnostics to outputs/evaluations/guardrail_evaluation_results.json.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.services.guardrails import (
    evaluate_retrieval_strength,
    format_guardrail_report,
    guarded_answer,
    retrieval_is_strong,
)

OUTPUT_DIR = Path("outputs/evaluations")
OUTPUT_FILE = OUTPUT_DIR / "guardrail_evaluation_results.json"

DEMONSTRATION_SCENARIOS = [
    {
        "name": "Scenario 1: Strong Retrieval (In-Domain Query)",
        "question": "What evidence supports the advisory fee charged to Marcus?",
        "chunks": [
            {
                "rank": 1,
                "score": 0.9420,
                "text": "Client Advisory Billing Evidence: Advisory fee of $1,250.00 for Q3 wealth advisory services was charged to Marcus on 20 August 2026, confirmed via invoice #INV-2026-08.",
                "metadata": {
                    "source": "client-billing-records.pdf",
                    "chunk_index": 1,
                    "document_id": "doc_billing_01",
                },
                "id": "doc_billing_01:1",
            },
            {
                "rank": 2,
                "score": 0.8910,
                "text": "Standard Fee Schedule: The annual advisory fee is 0.75% of assets under management, calculated and deducted on a quarterly basis in arrears.",
                "metadata": {
                    "source": "fee-schedule.pdf",
                    "chunk_index": 0,
                    "document_id": "doc_fee_01",
                },
                "id": "doc_fee_01:0",
            },
        ],
        "expected_status": "answered",
        "mock_answer": "Marcus was charged an advisory fee of $1,250.00 on 20 August 2026 confirmed via invoice #INV-2026-08 [1].",
    },
    {
        "name": "Scenario 2: Weak Retrieval (Out-of-Domain Query)",
        "question": "What is the corporate cafeteria weekly lunch special menu?",
        "chunks": [
            {
                "rank": 1,
                "score": 0.5420,
                "text": "Building Maintenance Notice: Elevator servicing will take place on Saturday morning.",
                "metadata": {
                    "source": "facility-notices.txt",
                    "chunk_index": 0,
                    "document_id": "doc_fac_01",
                },
                "id": "doc_fac_01:0",
            },
            {
                "rank": 2,
                "score": 0.4180,
                "text": "Visitor parking permits are available from the front desk upon presenting valid government ID.",
                "metadata": {
                    "source": "visitor-guidelines.md",
                    "chunk_index": 0,
                    "document_id": "doc_vis_01",
                },
                "id": "doc_vis_01:0",
            },
        ],
        "expected_status": "refused_weak_context",
        "mock_answer": None,
    },
    {
        "name": "Scenario 3: Empty Retrieval (Unknown Topic Query)",
        "question": "What is the cryptocurrency staking yield for Token XYZ?",
        "chunks": [],
        "expected_status": "refused_empty_context",
        "mock_answer": None,
    },
    {
        "name": "Scenario 4: Insufficient Supporting Chunks (High Minimum Requirement)",
        "question": "Provide two independent policy sources for the fixed deposit penalty rate.",
        "chunks": [
            {
                "rank": 1,
                "score": 0.8650,
                "text": "Term Deposit Terms: Fixed deposit early withdrawal incurs a 1.0% penalty fee.",
                "metadata": {
                    "source": "deposit-terms.pdf",
                    "chunk_index": 0,
                    "document_id": "doc_dep_01",
                },
                "id": "doc_dep_01:0",
            },
            {
                "rank": 2,
                "score": 0.5120,
                "text": "General bank branch operational hours from Monday to Friday.",
                "metadata": {
                    "source": "branch-hours.md",
                    "chunk_index": 0,
                    "document_id": "doc_hours_01",
                },
                "id": "doc_hours_01:0",
            },
        ],
        "min_supporting_chunks": 2,
        "expected_status": "refused_insufficient_support",
        "mock_answer": None,
    },
]


async def run_demonstration() -> Dict[str, Any]:
    """Execute guardrail demonstration across diverse scenarios and export evaluation payload."""
    print("=" * 70)
    print("FInee.ai - RETRIEVAL GUARDRAILS & SAFE REFUSAL DEMONSTRATION")
    print("=" * 70)

    print("\nGuardrail Configuration:")
    print("-" * 50)
    print(f"  MIN_TOP_SCORE          : {settings.MIN_TOP_SCORE}")
    print(f"  MIN_SUPPORTING_CHUNKS  : {settings.MIN_SUPPORTING_CHUNKS}")
    print(f"  RETRIEVAL_TOP_K        : {settings.RETRIEVAL_TOP_K}")
    print(f"  SAFE_REFUSAL_MESSAGE   : {settings.SAFE_REFUSAL_MESSAGE}")

    scenario_results = []

    for item in DEMONSTRATION_SCENARIOS:
        print("\n" + "=" * 70)
        print(f"Running: {item['name']}")
        print("=" * 70)

        chunks = item["chunks"]
        min_supp = item.get("min_supporting_chunks", settings.MIN_SUPPORTING_CHUNKS)

        # Pre-evaluate strength
        eval_res = evaluate_retrieval_strength(
            chunks=chunks,
            min_top_score=settings.MIN_TOP_SCORE,
            min_supporting_chunks=min_supp,
        )

        # Mock LLM generation for strong scenario
        if item.get("mock_answer"):
            with patch("src.services.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = item["mock_answer"]
                res = await guarded_answer(
                    question=item["question"],
                    chunks=chunks,
                    min_top_score=settings.MIN_TOP_SCORE,
                    min_supporting_chunks=min_supp,
                )
        else:
            res = await guarded_answer(
                question=item["question"],
                chunks=chunks,
                min_top_score=settings.MIN_TOP_SCORE,
                min_supporting_chunks=min_supp,
            )

        report = format_guardrail_report(res)
        print(report)

        scenario_results.append({
            "scenario": item["name"],
            "question": item["question"],
            "retrieved_chunks_count": len(chunks),
            "top_score": eval_res["top_score"],
            "supporting_chunks_count": eval_res["supporting_chunks_count"],
            "status": res["status"],
            "llm_called": res["metrics"]["llm_called"],
            "sources_count": len(res["sources"]),
            "refusal_reason": res.get("refusal_reason"),
            "response_sample": res["answer"][:100] + "..." if len(res["answer"]) > 100 else res["answer"],
        })

    # Export evaluation payload
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_payload = {
        "guardrail_configuration": {
            "min_top_score": settings.MIN_TOP_SCORE,
            "min_supporting_chunks": settings.MIN_SUPPORTING_CHUNKS,
            "retrieval_top_k": settings.RETRIEVAL_TOP_K,
            "safe_refusal_message": settings.SAFE_REFUSAL_MESSAGE,
        },
        "evaluation_summary": {
            "total_scenarios_evaluated": len(scenario_results),
            "refused_scenarios": sum(1 for s in scenario_results if s["status"] != "answered"),
            "answered_scenarios": sum(1 for s in scenario_results if s["status"] == "answered"),
            "llm_calls_prevented": sum(1 for s in scenario_results if not s["llm_called"]),
        },
        "scenario_evaluations": scenario_results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print(f"\nSaved demonstration evaluation to: {OUTPUT_FILE}")
    return results_payload


if __name__ == "__main__":
    asyncio.run(run_demonstration())
