"""Demonstration script for candidate re-ranking in finee.ai RAG platform.

Retrieves a larger candidate set (k=10) via initial vector search, applies relevance-based
re-ranking to score query/chunk pairs, and returns refined top-k results (final_k=3)
with before/after ranking comparisons and timing metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.retrieval.reranker import format_rerank_comparison, rerank, retrieve_and_rerank
from src.retrieval.retriever import retrieve
from src.retrieval.vector_store import InMemoryVectorStore

OUTPUT_DIR = Path("outputs/evaluations")
OUTPUT_FILE = OUTPUT_DIR / "reranking_demonstration_results.json"

SAMPLE_CORPUS = [
    {
        "id": "doc_general_01:0",
        "text": "General Wealth Advisory Commentary: Financial advisory clients like Marcus receive quarterly market outlook updates and wealth management advice.",
        "metadata": {
            "source": "general-wealth-guide.md",
            "document_id": "doc_general_01",
            "chunk_index": 0,
            "section": "General Overview",
            "approval_status": "approved",
        },
        "embedding": [0.82, 0.40, 0.20, 0.15, 0.10],
    },
    {
        "id": "doc_billing_01:1",
        "text": "Client Advisory Billing Evidence: Advisory fee of $1,250.00 for Q3 wealth advisory services was charged to Marcus on 20 August 2026, confirmed via invoice #INV-2026-08.",
        "metadata": {
            "source": "client-billing-records.pdf",
            "document_id": "doc_billing_01",
            "chunk_index": 1,
            "section": "Invoice Verification",
            "approval_status": "approved",
        },
        "embedding": [0.88, 0.35, 0.15, 0.20, 0.10],
    },
    {
        "id": "doc_fee_01:0",
        "text": "Standard Fee Schedule: The annual advisory fee is 0.75% of assets under management, calculated and deducted on a quarterly basis in arrears.",
        "metadata": {
            "source": "fee-schedule.pdf",
            "document_id": "doc_fee_01",
            "chunk_index": 0,
            "section": "Fee Schedule",
            "approval_status": "approved",
        },
        "embedding": [0.85, 0.30, 0.25, 0.10, 0.10],
    },
    {
        "id": "doc_fund_01:0",
        "text": "Balanced Bond Fund Factsheet: The bond portfolio matures on 31 December 2030 with an annual distribution yield of 4.2%.",
        "metadata": {
            "source": "fund-factsheet.pdf",
            "document_id": "doc_fund_01",
            "chunk_index": 0,
            "section": "Bond Yields",
            "approval_status": "approved",
        },
        "embedding": [0.30, 0.85, 0.20, 0.10, 0.10],
    },
    {
        "id": "doc_kyc_01:0",
        "text": "Customer Due Diligence: Identity verification requires a government-issued photo ID and proof of residence under KYC regulations.",
        "metadata": {
            "source": "compliance-policy.pdf",
            "document_id": "doc_kyc_01",
            "chunk_index": 0,
            "section": "KYC Identity",
            "approval_status": "approved",
        },
        "embedding": [0.20, 0.25, 0.88, 0.15, 0.10],
    },
    {
        "id": "doc_sec_01:0",
        "text": "Account Security Policy: Password resets require mandatory two-factor authentication (2FA) and a 12-character passphrase.",
        "metadata": {
            "source": "account-security.pdf",
            "document_id": "doc_sec_01",
            "chunk_index": 0,
            "section": "Security Controls",
            "approval_status": "approved",
        },
        "embedding": [0.15, 0.15, 0.20, 0.90, 0.10],
    },
    {
        "id": "doc_deposit_01:0",
        "text": "Term Deposit Agreement: Early withdrawal before the 12-month fixed term forfeits 3 months of accrued interest.",
        "metadata": {
            "source": "deposit-agreement.pdf",
            "document_id": "doc_deposit_01",
            "chunk_index": 0,
            "section": "Withdrawal Rules",
            "approval_status": "approved",
        },
        "embedding": [0.10, 0.20, 0.15, 0.10, 0.92],
    },
    {
        "id": "doc_advisory_contract:0",
        "text": "Advisory Agreement Terms: Clients agree to electronic fee debiting from their linked primary settlement account upon invoice issuance.",
        "metadata": {
            "source": "advisory-agreement.pdf",
            "document_id": "doc_advisory_contract",
            "chunk_index": 0,
            "section": "Billing Consent",
            "approval_status": "approved",
        },
        "embedding": [0.80, 0.28, 0.22, 0.12, 0.15],
    },
    {
        "id": "doc_tax_01:0",
        "text": "Annual Tax Reporting: Year-end statements compile all advisory fees and realized capital gains for tax deduction purposes.",
        "metadata": {
            "source": "tax-guide.pdf",
            "document_id": "doc_tax_01",
            "chunk_index": 0,
            "section": "Tax Disclosures",
            "approval_status": "approved",
        },
        "embedding": [0.70, 0.30, 0.20, 0.15, 0.20],
    },
    {
        "id": "doc_portal_01:0",
        "text": "Client Portal User Guide: Clients can view payment history and download signed fee receipts through the online portal.",
        "metadata": {
            "source": "client-portal.md",
            "document_id": "doc_portal_01",
            "chunk_index": 0,
            "section": "Portal Usage",
            "approval_status": "approved",
        },
        "embedding": [0.75, 0.25, 0.20, 0.20, 0.15],
    },
]


def run_reranking_demonstration() -> Dict[str, Any]:
    """Execute the re-ranking demonstration workflow and save results."""
    print("=" * 70)
    print("FInee.ai - CANDIDATE RE-RANKING DEMONSTRATION")
    print("=" * 70)

    # 1. Setup in-memory vector store with sample corpus
    store = InMemoryVectorStore(name="demo_rerank_chunks")
    store.add(SAMPLE_CORPUS)

    query = "What evidence supports the advisory fee charged to the client?"
    candidate_k = 10
    final_k = 3

    print(f"\nQuery: {query}")
    print(f"Retrieval Candidate K: {candidate_k} -> Re-ranking Final K: {final_k}")
    print("-" * 70)

    # 2. Initial vector retrieval
    t0 = time.perf_counter()
    query_vector = [0.85, 0.35, 0.15, 0.15, 0.10]
    raw_search = store.search(query_vector=query_vector, top_k=candidate_k)
    t1 = time.perf_counter()
    retrieval_latency = t1 - t0

    initial_candidates: List[Dict[str, Any]] = []
    for item in raw_search:
        initial_candidates.append({
            "rank": item["rank"],
            "score": round(item["score"], 4),
            "text": item["text"],
            "metadata": item["metadata"],
            "id": item.get("id"),
        })

    # 3. Apply Re-ranking
    t2 = time.perf_counter()
    reranked_results = rerank(query=query, candidates=initial_candidates, final_k=final_k)
    t3 = time.perf_counter()
    rerank_latency = t3 - t2
    total_latency = t3 - t0

    result_payload: Dict[str, Any] = {
        "status": "success",
        "query": query,
        "candidate_k": candidate_k,
        "final_k": final_k,
        "initial_candidates": initial_candidates,
        "reranked_results": reranked_results,
        "metrics": {
            "candidate_count": len(initial_candidates),
            "final_count": len(reranked_results),
            "retrieval_latency_seconds": round(retrieval_latency, 4),
            "rerank_latency_seconds": round(rerank_latency, 4),
            "total_latency_seconds": round(total_latency, 4),
            "rerank_calls": len(initial_candidates),
        },
    }

    # 4. Display formatted before/after comparison
    comparison_text = format_rerank_comparison(result_payload)
    print("\n" + comparison_text)

    # 5. Save evaluation output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2)
    print(f"\nSaved demonstration results to: {OUTPUT_FILE}")

    return result_payload


def main() -> None:
    run_reranking_demonstration()


if __name__ == "__main__":
    main()
