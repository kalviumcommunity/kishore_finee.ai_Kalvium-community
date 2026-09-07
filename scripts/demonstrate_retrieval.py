"""Demonstration script for Similarity Search & Top-K Retrieval in finee.ai.

Demonstrates:
1. Embedding user queries using the exact same embedding model as document chunks.
2. Running top-k cosine similarity search against an indexed vector database collection.
3. Returning retrieved chunks with similarity scores, source text, and provenance metadata.
4. Demonstrating how changing k (k=1, k=3, k=5) changes the retrieved context.
5. Exporting structured query results to outputs/evaluations/.
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
from src.embeddings.embedding_service import EmbeddingService, get_embedding_service
from src.retrieval.chroma_store import ChromaVectorStore
from src.retrieval.retriever import _embed_query_safe, compare_k_retrieval, retrieve
from src.retrieval.vector_store import InMemoryVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demonstrate_retrieval")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "evaluations"
OUTPUT_FILE_PRIMARY = OUTPUT_DIR / "similarity_search_retrieval_results.json"
OUTPUT_FILE_DEMO = OUTPUT_DIR / "top_k_retrieval_demo.json"


# Sample financial advisory and account onboarding corpus chunks
CORPUS_CHUNKS: List[Dict[str, Any]] = [
    {
        "text": (
            "To reset your account password, navigate to the FInee.ai login portal and click 'Forgot Password'. "
            "Enter your registered email address to receive a secure time-limited one-time password (OTP) verification link."
        ),
        "metadata": {
            "source": "auth-and-access-guide.md",
            "document_id": "doc_sec_001",
            "chunk_index": 0,
            "section": "Password Management",
            "page": 1,
            "approval_status": "approved",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": (
            "If a learner or client forgets their login credentials, they can reset their password through the self-service portal "
            "or contact support desk with their verified two-factor authentication (2FA) device for immediate account recovery."
        ),
        "metadata": {
            "source": "auth-and-access-guide.md",
            "document_id": "doc_sec_001",
            "chunk_index": 1,
            "section": "Account Recovery",
            "page": 2,
            "approval_status": "approved",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": (
            "Mutual funds pool money from multiple retail and institutional investors to construct a diversified portfolio "
            "of equity shares, government bonds, money market instruments, or precious metals managed by professional fund managers."
        ),
        "metadata": {
            "source": "mutual-fund-handbook.pdf",
            "document_id": "doc_mf_101",
            "chunk_index": 0,
            "section": "Fund Fundamentals",
            "page": 3,
            "approval_status": "approved",
            "effective_date": "2026-01-15",
        },
    },
    {
        "text": (
            "Equity mutual funds allocate at least 65% of assets into company equities and growth shares. "
            "While they offer higher long-term capital appreciation potential, they carry market volatility risk."
        ),
        "metadata": {
            "source": "mutual-fund-handbook.pdf",
            "document_id": "doc_mf_101",
            "chunk_index": 1,
            "section": "Equity Fund Classification",
            "page": 4,
            "approval_status": "approved",
            "effective_date": "2026-01-15",
        },
    },
    {
        "text": (
            "A mutual fund's Total Expense Ratio (TER) represents the annual operating cost, including management fees, "
            "administrative expenses, and distribution commissions expressed as an annualized percentage of the fund's daily net assets."
        ),
        "metadata": {
            "source": "mutual-fund-handbook.pdf",
            "document_id": "doc_mf_101",
            "chunk_index": 2,
            "section": "Expense Ratios and Fee Structures",
            "page": 7,
            "approval_status": "approved",
            "effective_date": "2026-01-15",
        },
    },
    {
        "text": (
            "Debt mutual funds invest in fixed-income securities like sovereign treasury bills, corporate debentures, and commercial paper. "
            "Debt fund performance is sensitive to central bank interest rate fluctuations and macroeconomic credit default risks."
        ),
        "metadata": {
            "source": "debt-instruments-overview.pdf",
            "document_id": "doc_debt_201",
            "chunk_index": 0,
            "section": "Fixed Income Mechanics",
            "page": 2,
            "approval_status": "approved",
            "effective_date": "2026-02-01",
        },
    },
    {
        "text": (
            "Regulatory compliance disclaimer: Past performance is not indicative of future returns. "
            "All investment decisions are subject to market risks, and clients must read scheme offer documents carefully before investing."
        ),
        "metadata": {
            "source": "compliance-disclosures-sebi.md",
            "document_id": "doc_comp_301",
            "chunk_index": 0,
            "section": "Mandatory Statutory Disclaimers",
            "page": 1,
            "approval_status": "approved",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": (
            "The company cafeteria menu features Italian pasta, chef specials, and fresh salads on alternating Tuesdays and Thursdays."
        ),
        "metadata": {
            "source": "office-cafeteria-bulletin.txt",
            "document_id": "doc_misc_999",
            "chunk_index": 0,
            "section": "Dining and Lunch",
            "page": 1,
            "approval_status": "approved",
            "effective_date": "2026-03-01",
        },
    },
]


def build_demo_vector_store(
    embedding_service: EmbeddingService,
) -> InMemoryVectorStore:
    """Index sample corpus chunks into an in-memory vector store."""
    store = InMemoryVectorStore(name="finee_financial_corpus")
    logger.info("Indexing %d sample chunks into vector store...", len(CORPUS_CHUNKS))
    store.add_chunks(CORPUS_CHUNKS, embedding_service=embedding_service)
    logger.info("Successfully indexed %d records with model: %s", store.count(), embedding_service.model)
    return store


def run_retrieval_demonstration() -> Dict[str, Any]:
    """Execute complete retrieval demonstration fulfilling all tasks."""
    service = get_embedding_service()
    store = build_demo_vector_store(service)

    print("\n" + "=" * 75)
    print("  FInee.ai - SIMILARITY SEARCH & TOP-K RETRIEVAL PIPELINE")
    print("=" * 75)
    print(f"Embedding Model  : {service.model}")
    print(f"Indexed Chunks   : {store.count()}")
    print(f"API Configured   : {bool(service.api_key)}")
    print("=" * 75)

    sample_query = "How can a learner reset their password?"

    # -------------------------------------------------------------
    # Task 1: Embed User Query with the Same Model
    # -------------------------------------------------------------
    print("\n[Task 1] - EMBED THE USER QUERY")
    print("-" * 75)
    print(f"Query Text: \"{sample_query}\"")
    query_vector = _embed_query_safe(service, sample_query)
    print(f"Embedding Model Used : {service.model} (Identical to document chunks)")
    print(f"Vector Dimension     : {len(query_vector)}")
    print(f"Vector Preview       : [{', '.join(f'{v:.4f}' for v in query_vector[:6])}, ...]")

    # -------------------------------------------------------------
    # Task 2 & Task 3: Top-K Similarity Search with Scores & Metadata
    # -------------------------------------------------------------
    print("\n[Task 2 & 3] - TOP-K SIMILARITY SEARCH WITH SCORES & METADATA (k=3)")
    print("-" * 75)
    results_k3 = retrieve(
        query=sample_query,
        k=3,
        collection=store,
        embedding_service=service,
    )

    for result in results_k3:
        print(f"rank        : {result['rank']}")
        print(f"score       : {result['score']:.4f}")
        print(f"source      : {result['metadata']['source']}")
        print(f"chunk_index : {result['metadata']['chunk_index']}")
        print(f"section     : {result['metadata'].get('section', 'N/A')}")
        print(f"text        : {result['text']}")
        print("-" * 50)

    # -------------------------------------------------------------
    # Task 4: Demonstrate Changing k (k=1, 3, 5)
    # -------------------------------------------------------------
    print("\n[Task 4] - DEMONSTRATE CHANGING K (k=1, k=3, k=5)")
    print("-" * 75)
    k_comparison = compare_k_retrieval(
        query=sample_query,
        k_values=[1, 3, 5],
        collection=store,
        embedding_service=service,
    )

    for k in [1, 3, 5]:
        print(f"\n--- k = {k} ---")
        for res in k_comparison["results_by_k"][f"k_{k}"]:
            print(f"  Score: {res['score']:.4f} | Source: {res['source']} [Chunk {res['chunk_index']}]")
            print(f"  Snippet: {res['text_snippet']}")

    print("\n--- Trade-off Analysis Across k Values ---")
    for summary in k_comparison["comparison_summary"]:
        print(
            f"k={summary['k']}: {summary['total_chunks_returned']} chunks returned, "
            f"Score range: [{summary['min_score_at_k']:.4f} - {summary['max_score_at_k']:.4f}]"
        )

    # -------------------------------------------------------------
    # ChromaDB Vector Database Demonstration
    # -------------------------------------------------------------
    print("\n[ChromaDB Integration] - CHROMADB TOP-K RETRIEVAL")
    print("-" * 75)
    chroma_store = ChromaVectorStore(collection_name="finee_demo_chroma")
    chroma_store.clear()
    chroma_store.add_chunks(CORPUS_CHUNKS, embedding_service=service)
    print(f"ChromaDB Collection : {chroma_store.collection_name}")
    print(f"ChromaDB Chunks Count: {chroma_store.count()}")

    chroma_k3_results = retrieve(
        query=sample_query,
        k=3,
        collection=chroma_store,
        embedding_service=service,
    )
    for r in chroma_k3_results:
        print(f"  [Chroma Rank {r['rank']}] Score: {r['score']:.4f} | Source: {r['metadata'].get('source')} | Text: {r['text'][:80]}...")

    # -------------------------------------------------------------
    # Task 5: Execute and Commit Multiple Sample Query Results
    # -------------------------------------------------------------
    print("\n[Task 5] - SAMPLE QUERIES EXECUTION & JSON EXPORT")
    print("-" * 75)

    test_queries = [
        "How can a learner reset their password?",
        "What is a mutual fund's Total Expense Ratio (TER) and operating cost?",
        "How do interest rate fluctuations affect debt mutual funds?",
        "What are the mandatory compliance disclaimers for investment risks?",
    ]

    query_results_payload: List[Dict[str, Any]] = []

    for q in test_queries:
        logger.info("Executing retrieval for query: '%s'", q)
        q_comp = compare_k_retrieval(
            query=q,
            k_values=[1, 3, 5],
            collection=store,
            embedding_service=service,
        )
        query_results_payload.append(q_comp)

    # Prepare structured summary output
    evaluation_output = {
        "status": "success",
        "timestamp": "2026-09-07T13:20:00Z",
        "embedding_model": service.model,
        "total_corpus_chunks": store.count(),
        "primary_demonstration_query": sample_query,
        "sample_retrieval_k3": results_k3,
        "chromadb_retrieval_k3": chroma_k3_results,
        "k_tradeoff_demonstration": k_comparison,
        "all_queries_evaluated": query_results_payload,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE_PRIMARY, "w", encoding="utf-8") as f:
        json.dump(evaluation_output, f, indent=2)
    logger.info("Saved primary evaluation results to: %s", OUTPUT_FILE_PRIMARY)

    with open(OUTPUT_FILE_DEMO, "w", encoding="utf-8") as f:
        json.dump({
            "query": sample_query,
            "embedding_model": service.model,
            "results_by_k": k_comparison["results_by_k"],
            "comparison_summary": k_comparison["comparison_summary"],
        }, f, indent=2)
    logger.info("Saved demo results to: %s", OUTPUT_FILE_DEMO)

    print(f"\nSuccessfully wrote results to:\n  - {OUTPUT_FILE_PRIMARY}\n  - {OUTPUT_FILE_DEMO}")
    print("=" * 75 + "\n")

    return evaluation_output


def main() -> None:
    """Entry point for CLI execution."""
    run_retrieval_demonstration()


if __name__ == "__main__":
    main()
