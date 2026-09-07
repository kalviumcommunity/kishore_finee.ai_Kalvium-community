"""Demonstration script for Batch Embedding & Rate/Cost Management.

Demonstrates:
1. Batching document chunks with configurable batch sizes to reduce API overhead.
2. Handling rate-limit and transient API errors via exponential backoff retries.
3. Tracking input tokens and calculating approximate embedding costs.
4. Detecting and skipping already-embedded chunks on re-runs for complete idempotency.
5. Emitting comprehensive run summaries and saving execution artifacts to JSON.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.embeddings.batch_embedder import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_PRICE_PER_1K_TOKENS,
    BatchEmbedder,
    BatchRunSummary,
    batches,
)
from src.embeddings.embedder import _generate_deterministic_semantic_vector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("batch_embedding_demo")

OUTPUT_FILE = PROJECT_ROOT / "outputs" / "evaluations" / "batch_embedding_summary.json"


def get_sample_financial_chunks() -> List[Dict[str, Any]]:
    """Build a realistic sample corpus of financial advisory chunks."""
    return [
        {
            "id": "chunk_001",
            "text": "FInee.ai Wealth Management Advisory provides personalized asset allocation and risk assessment.",
            "metadata": {"source": "wealth_overview.pdf", "section": "Introduction", "page": 1},
        },
        {
            "id": "chunk_002",
            "text": "High-yield savings accounts currently offer up to 4.85% APY with FDIC insurance up to $250,000.",
            "metadata": {"source": "savings_rates_2026.pdf", "section": "Yield Table", "page": 3},
        },
        {
            "id": "chunk_003",
            "text": "Portfolio rebalancing should occur quarterly or whenever asset weights drift by more than 5%.",
            "metadata": {"source": "investment_policy.pdf", "section": "Rebalancing", "page": 7},
        },
        {
            "id": "chunk_004",
            "text": "Roth IRA contributions are made with after-tax dollars and qualified withdrawals are tax-free.",
            "metadata": {"source": "retirement_planning.pdf", "section": "Tax Accounts", "page": 12},
        },
        {
            "id": "chunk_005",
            "text": "Emergency funds should cover 3 to 6 months of essential living expenses in liquid cash instruments.",
            "metadata": {"source": "personal_finance_guide.pdf", "section": "Safety Net", "page": 2},
        },
        {
            "id": "chunk_006",
            "text": "Dollar-cost averaging mitigates market volatility by investing fixed dollar amounts at regular intervals.",
            "metadata": {"source": "investment_policy.pdf", "section": "Strategies", "page": 9},
        },
        {
            "id": "chunk_007",
            "text": "Municipal bonds generally offer interest earnings exempt from federal income taxes for eligible investors.",
            "metadata": {"source": "fixed_income.pdf", "section": "Bonds", "page": 4},
        },
        {
            "id": "chunk_008",
            "text": "Capital gains tax rates apply to assets held for over one year before liquidation.",
            "metadata": {"source": "tax_strategies.pdf", "section": "Capital Gains", "page": 5},
        },
        {
            "id": "chunk_009",
            "text": "Estate planning documents should include a revocable living trust, power of attorney, and healthcare directive.",
            "metadata": {"source": "estate_planning.pdf", "section": "Checklist", "page": 1},
        },
        {
            "id": "chunk_010",
            "text": "Index funds provide broad market exposure with low expense ratios and minimal turnover.",
            "metadata": {"source": "investment_policy.pdf", "section": "Fund Types", "page": 11},
        },
        {
            "id": "chunk_011",
            "text": "Compound interest accelerates wealth accumulation when earnings are continuously reinvested.",
            "metadata": {"source": "personal_finance_guide.pdf", "section": "Growth", "page": 6},
        },
        {
            "id": "chunk_012",
            "text": "401(k) employer matching contributions represent immediate 100% return on invested funds up to the cap.",
            "metadata": {"source": "retirement_planning.pdf", "section": "Employer Plans", "page": 15},
        },
    ]


def run_batch_embedding_demonstration() -> Dict[str, Any]:
    """Execute complete batch embedding demonstration covering all tasks."""
    print("=" * 80)
    print("FInee.ai - Batch Embedding & Rate/Cost Management Pipeline")
    print("=" * 80)

    corpus = get_sample_financial_chunks()
    batch_size = 4  # Configurable batch size to demonstrate multiple batches
    price_per_1k = DEFAULT_PRICE_PER_1K_TOKENS

    print(f"\n[Configuration]")
    print(f"  • Total Chunks in Corpus : {len(corpus)}")
    print(f"  • Configured Batch Size  : {batch_size}")
    print(f"  • Model Price per 1K Tkns: ${price_per_1k:.5f}")

    # =========================================================================
    # Task 1 & 2: Batching and Exponential Backoff Retry Demonstration
    # =========================================================================
    print("\n" + "-" * 80)
    print("[Task 1 & 2] Batch Embedding & Simulated Rate-Limit Retry Handling")
    print("-" * 80)

    # Track simulated transient rate limit error on batch 2
    attempt_counters: Dict[str, int] = {"count": 0}

    def robust_mock_embed(texts: List[str]) -> List[List[float]]:
        """Simulate transient 429 Rate Limit error on first encounter to demonstrate retry."""
        attempt_counters["count"] += 1
        # Trigger transient error on the 2nd API request (attempt 1)
        if attempt_counters["count"] == 2:
            raise ConnectionError("429 Too Many Requests (Rate limit exceeded, retry after backoff)")
        return [_generate_deterministic_semantic_vector(t) for t in texts]

    batch_embedder = BatchEmbedder(
        batch_size=batch_size,
        max_attempts=3,
        price_per_1k_tokens=price_per_1k,
        embed_fn=robust_mock_embed,
        initial_wait=0.05,  # Short wait for demo speed
    )

    print("\nStarting Initial Run 1 (Cold Start - Empty Cache)...")
    start_time_run1 = time.time()
    embeddings_store, summary_run1 = batch_embedder.process_corpus(
        all_chunks=corpus,
        existing_embeddings=None,
        batch_size=batch_size,
    )
    elapsed_run1 = time.time() - start_time_run1

    print("\n[Run 1 Summary - Initial Embedding]")
    print(f"  • Total Chunks       : {summary_run1.total_chunks}")
    print(f"  • Skipped Existing   : {summary_run1.skipped_existing}")
    print(f"  • Embedded Chunks    : {summary_run1.embedded}")
    print(f"  • Failed Chunks      : {summary_run1.failed}")
    print(f"  • Batches Processed  : {summary_run1.batches_processed}")
    print(f"  • Retries Handled    : {summary_run1.retry_count}")
    print(f"  • Total Input Tokens : {summary_run1.input_tokens}")
    print(f"  • Estimated Cost     : ${summary_run1.estimated_cost_usd:.6f} USD")
    print(f"  • Elapsed Time       : {elapsed_run1:.3f}s")

    # =========================================================================
    # Task 3: Reporting Totals & Cost
    # =========================================================================
    print("\n" + "-" * 80)
    print("[Task 3] Totals and Cost Calculation Verification")
    print("-" * 80)
    expected_cost = (summary_run1.input_tokens / 1000.0) * price_per_1k
    print(f"  Formula: ({summary_run1.input_tokens} tokens / 1000) * ${price_per_1k:.5f} = ${expected_cost:.6f} USD")
    print(f"  Reported Cost: ${summary_run1.estimated_cost_usd:.6f} USD (Match: {abs(summary_run1.estimated_cost_usd - expected_cost) < 1e-9})")

    # =========================================================================
    # Task 4: Re-run Idempotency (Skip already-embedded chunks)
    # =========================================================================
    print("\n" + "-" * 80)
    print("[Task 4] Skip Already-Embedded Chunks on Re-Run")
    print("-" * 80)
    print("Starting Re-Run 2 on the exact same corpus using existing embeddings store...")

    start_time_run2 = time.time()
    embeddings_store_run2, summary_run2 = batch_embedder.process_corpus(
        all_chunks=corpus,
        existing_embeddings=embeddings_store,
        batch_size=batch_size,
    )
    elapsed_run2 = time.time() - start_time_run2

    print("\n[Run 2 Summary - Re-Run / Idempotent]")
    print(f"  • Total Chunks       : {summary_run2.total_chunks}")
    print(f"  • Skipped Existing   : {summary_run2.skipped_existing} (100% Skipped!)")
    print(f"  • Embedded Chunks    : {summary_run2.embedded}")
    print(f"  • Failed Chunks      : {summary_run2.failed}")
    print(f"  • Batches Processed  : {summary_run2.batches_processed}")
    print(f"  • Total Input Tokens : {summary_run2.input_tokens}")
    print(f"  • Estimated Cost     : ${summary_run2.estimated_cost_usd:.6f} USD ($0 wasted cost!)")
    print(f"  • Elapsed Time       : {elapsed_run2:.3f}s")

    # =========================================================================
    # Incremental Addition (Partial re-run with new chunks)
    # =========================================================================
    print("\n" + "-" * 80)
    print("[Incremental Run] Appending New Chunks to Existing Corpus")
    print("-" * 80)
    new_chunks = [
        {
            "id": "chunk_013",
            "text": "Health Savings Accounts (HSAs) offer triple-tax advantages for eligible medical expenses.",
            "metadata": {"source": "healthcare_planning.pdf", "page": 8},
        },
        {
            "id": "chunk_014",
            "text": "Annuities provide guaranteed lifetime income streams for risk-averse retirees.",
            "metadata": {"source": "annuities_guide.pdf", "page": 3},
        },
    ]
    augmented_corpus = corpus + new_chunks
    print(f"Augmented Corpus size: {len(augmented_corpus)} chunks (12 existing + 2 new)")

    embeddings_store_run3, summary_run3 = batch_embedder.process_corpus(
        all_chunks=augmented_corpus,
        existing_embeddings=embeddings_store_run2,
        batch_size=batch_size,
    )

    print("\n[Run 3 Summary - Incremental]")
    print(f"  • Total Chunks       : {summary_run3.total_chunks}")
    print(f"  • Skipped Existing   : {summary_run3.skipped_existing}")
    print(f"  • Embedded Chunks    : {summary_run3.embedded} (Only the 2 new chunks)")
    print(f"  • Input Tokens       : {summary_run3.input_tokens}")
    print(f"  • Estimated Cost     : ${summary_run3.estimated_cost_usd:.6f} USD")

    # =========================================================================
    # Task 5: Structured Run Summary Artifact
    # =========================================================================
    output_payload: Dict[str, Any] = {
        "status": "success",
        "pipeline": "BatchEmbedder",
        "batch_size": batch_size,
        "price_per_1k_tokens": price_per_1k,
        "initial_run": summary_run1.to_dict(),
        "rerun_identical": summary_run2.to_dict(),
        "incremental_run": summary_run3.to_dict(),
        "verification": {
            "batching_functional": summary_run1.batches_processed > 1,
            "retry_handled_successfully": summary_run1.retry_count >= 1,
            "rerun_skipped_all_existing": summary_run2.skipped_existing == len(corpus),
            "rerun_zero_cost": summary_run2.estimated_cost_usd == 0.0,
            "incremental_only_embedded_new": summary_run3.embedded == len(new_chunks),
        },
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Run summary artifact successfully generated: {OUTPUT_FILE}")
    print("=" * 80)

    return output_payload


if __name__ == "__main__":
    run_batch_embedding_demonstration()
