"""Demonstration script for Metadata Filtering & Hybrid Search in finee.ai RAG platform.

Demonstrates:
1. Restricting vector retrieval using metadata filters (source, section, category, document_type).
2. Comparing filtered and unfiltered results for financial advisory and compliance queries.
3. Combining vector semantic similarity with exact keyword matching (hybrid ranking).
4. Demonstrating precision improvements by eliminating plausible out-of-scope distractor chunks.
5. Exporting structured execution results to outputs/evaluations/.
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
from src.retrieval.retriever import (
    compare_filtered_unfiltered,
    hybrid_rank,
    hybrid_retrieve,
    keyword_score,
    retrieve,
    show_results,
)
from src.retrieval.vector_store import InMemoryVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demonstrate_filtered_hybrid")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "evaluations"
OUTPUT_FILE_PRIMARY = OUTPUT_DIR / "metadata_filtering_hybrid_search_results.json"
OUTPUT_FILE_DEMO = OUTPUT_DIR / "filtered_hybrid_search_demo.json"


# Rich financial advisory and compliance corpus with diverse metadata fields
CORPUS_CHUNKS: List[Dict[str, Any]] = [
    {
        "text": (
            "To reset your account password, navigate to the FInee.ai login portal and click 'Forgot Password'. "
            "Enter your registered email address to receive a secure time-limited one-time password (OTP) verification link."
        ),
        "metadata": {
            "source": "auth-and-access-guide.md",
            "document_id": "doc_auth_001",
            "chunk_index": 0,
            "section": "Account access",
            "category": "account_management",
            "department": "client_services",
            "user_role": "retail_investor",
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
            "document_id": "doc_auth_001",
            "chunk_index": 1,
            "section": "Account access",
            "category": "account_management",
            "department": "client_services",
            "user_role": "retail_investor",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": (
            "Internal enterprise IT policy requires all employee root credentials and admin accounts to enforce 90-day password "
            "rotation, 16-character passphrase complexity, and automated lockouts upon 3 consecutive failed attempts."
        ),
        "metadata": {
            "source": "internal-it-security-policy.pdf",
            "document_id": "doc_sec_999",
            "chunk_index": 0,
            "section": "Enterprise Infrastructure Security",
            "category": "internal_it",
            "department": "information_security",
            "user_role": "internal_employee",
            "effective_date": "2025-11-01",
        },
    },
    {
        "text": (
            "Under Section 80C of the Income Tax Act, individual taxpayers can claim deductions up to Rs 1,50,000 per financial year "
            "for investments in Equity Linked Savings Schemes (ELSS), Public Provident Fund (PPF), National Savings Certificate (NSC), and life insurance premiums."
        ),
        "metadata": {
            "source": "tax-planning-handbook-2026.pdf",
            "document_id": "doc_tax_201",
            "chunk_index": 0,
            "section": "Section 80C Deductions",
            "category": "taxation",
            "department": "wealth_advisory",
            "user_role": "retail_investor",
            "effective_date": "2026-04-01",
        },
    },
    {
        "text": (
            "Section 54 of the Income Tax Act provides capital gains tax exemption on long-term capital gains arising from the transfer of a residential house property, "
            "provided the net sale proceeds are reinvested in acquiring or constructing another residential house in India."
        ),
        "metadata": {
            "source": "tax-planning-handbook-2026.pdf",
            "document_id": "doc_tax_201",
            "chunk_index": 1,
            "section": "Capital Gains Exemptions",
            "category": "taxation",
            "department": "wealth_advisory",
            "user_role": "retail_investor",
            "effective_date": "2026-04-01",
        },
    },
    {
        "text": (
            "SEBI Circular SEBI/HO/MIRSD/DOS3/CIR/P/2026/42 mandates digital Aadhaar-based e-KYC and video customer identification "
            "process (V-CIP) for all high-net-worth client onboarding and portfolio management service (PMS) agreements."
        ),
        "metadata": {
            "source": "sebi-compliance-compendium-2026.pdf",
            "document_id": "doc_reg_301",
            "chunk_index": 0,
            "section": "KYC and Onboarding Compliance",
            "category": "regulatory_compliance",
            "department": "compliance_office",
            "compliance_code": "SEBI-CIR-2026-42",
            "user_role": "compliance_officer",
            "effective_date": "2026-02-15",
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
            "category": "mutual_funds",
            "department": "wealth_advisory",
            "user_role": "retail_investor",
            "effective_date": "2026-01-15",
        },
    },
]


def setup_in_memory_collection(service: EmbeddingService) -> InMemoryVectorStore:
    """Initialize and populate an InMemoryVectorStore collection."""
    store = InMemoryVectorStore(name="finee_metadata_collection")
    store.add_chunks(CORPUS_CHUNKS, embedding_service=service)
    logger.info("Indexed %d records into InMemoryVectorStore", store.count())
    return store


def setup_chroma_collection(service: EmbeddingService) -> ChromaVectorStore:
    """Initialize and populate a ChromaVectorStore collection."""
    chroma = ChromaVectorStore(
        collection_name="finee_metadata_filtering_demo",
        persist_directory="./outputs/data/chroma_filtered_demo",
    )
    chroma.add_chunks(CORPUS_CHUNKS, embedding_service=service)
    logger.info("Indexed %d records into ChromaVectorStore", chroma.count())
    return chroma


def run_demonstration() -> Dict[str, Any]:
    """Execute all 5 Tasks for Metadata Filtering & Hybrid Search."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    service = get_embedding_service()

    in_memory_store = setup_in_memory_collection(service)
    chroma_store = setup_chroma_collection(service)

    print("\n" + "=" * 75)
    print("  finee.ai RAG Platform: Metadata Filtering & Hybrid Search Demo")
    print("=" * 75)

    demo_results: Dict[str, Any] = {
        "metadata": {
            "embedding_model": service.model,
            "total_corpus_chunks": len(CORPUS_CHUNKS),
            "vector_stores_evaluated": ["InMemoryVectorStore", "ChromaVectorStore"],
        },
        "scenarios": {},
    }

    # =========================================================================
    # Scenario 1: Password Reset (Task 1 & 2 - Metadata Pre-filtering)
    # =========================================================================
    print("\n---------------------------------------------------------------------------")
    print("SCENARIO 1: Account Password Reset (Unfiltered vs Section Filtered)")
    print("Query: 'What are the password reset steps?'")
    print("Filter: {'section': 'Account access'}")
    print("---------------------------------------------------------------------------")

    query_1 = "What are the password reset steps?"
    filter_1 = {"section": "Account access"}
    keywords_1 = ["password", "reset", "otp", "login"]

    # 1. Unfiltered retrieval (searches whole corpus)
    unfiltered_1 = retrieve(query_1, k=3, collection=in_memory_store, embedding_service=service)
    show_results("Unfiltered Results (Whole Corpus)", unfiltered_1)

    # 2. Filtered retrieval (scoped to section = Account access)
    filtered_1 = retrieve(
        query_1,
        k=3,
        collection=in_memory_store,
        embedding_service=service,
        metadata_filter=filter_1,
    )
    show_results("Filtered Results (section = 'Account access')", filtered_1)

    # 3. Hybrid scoring with keyword matching
    hybrid_1 = hybrid_rank(filtered_1, keywords=keywords_1, vector_weight=0.8, keyword_weight=0.2)
    show_results("Hybrid Filtered Results (Vector 0.8 + Keywords 0.2)", hybrid_1)

    comp_1 = compare_filtered_unfiltered(
        query=query_1,
        filter_metadata=filter_1,
        keywords=keywords_1,
        k=3,
        collection=in_memory_store,
        embedding_service=service,
    )

    demo_results["scenarios"]["scenario_1_password_reset"] = comp_1

    # =========================================================================
    # Scenario 2: Tax Deductions (Task 4 - Precision Improvement via Filtering)
    # =========================================================================
    print("\n---------------------------------------------------------------------------")
    print("SCENARIO 2: Tax Deduction Advisory (Distractor Elimination)")
    print("Query: 'What is the maximum investment limit for tax deduction?'")
    print("Filter: {'category': 'taxation', 'section': 'Section 80C Deductions'}")
    print("---------------------------------------------------------------------------")

    query_2 = "What is the maximum investment limit for tax deduction?"
    filter_2 = {"category": "taxation", "section": "Section 80C Deductions"}
    keywords_2 = ["80c", "deduction", "1,50,000", "elss", "ppf"]

    comp_2 = compare_filtered_unfiltered(
        query=query_2,
        filter_metadata=filter_2,
        keywords=keywords_2,
        k=3,
        collection=in_memory_store,
        embedding_service=service,
    )
    show_results("Tax Query - Unfiltered", comp_2["unfiltered_results"])
    show_results("Tax Query - Filtered (Section 80C)", comp_2["filtered_results"])
    show_results("Tax Query - Hybrid Filtered", comp_2["hybrid_results"])

    demo_results["scenarios"]["scenario_2_tax_deductions"] = comp_2

    # =========================================================================
    # Scenario 3: Regulatory Compliance Code Matching (Task 3 - Hybrid Search)
    # =========================================================================
    print("\n---------------------------------------------------------------------------")
    print("SCENARIO 3: Compliance Circular Code Search (Exact Token Hybrid Match)")
    print("Query: 'What are the client onboarding rules under SEBI-CIR-2026-42?'")
    print("Filter: {'category': 'regulatory_compliance'}")
    print("Keywords: ['sebi-cir-2026-42', 'e-kyc', 'v-cip', 'aadhaar']")
    print("---------------------------------------------------------------------------")

    query_3 = "What are the client onboarding rules under SEBI-CIR-2026-42?"
    filter_3 = {"category": "regulatory_compliance"}
    keywords_3 = ["sebi-cir-2026-42", "e-kyc", "v-cip", "aadhaar", "pms"]

    comp_3 = compare_filtered_unfiltered(
        query=query_3,
        filter_metadata=filter_3,
        keywords=keywords_3,
        k=3,
        collection=in_memory_store,
        embedding_service=service,
    )
    show_results("Compliance Query - Unfiltered", comp_3["unfiltered_results"])
    show_results("Compliance Query - Filtered", comp_3["filtered_results"])
    show_results("Compliance Query - Hybrid Match", comp_3["hybrid_results"])

    demo_results["scenarios"]["scenario_3_regulatory_compliance"] = comp_3

    # =========================================================================
    # Scenario 4: ChromaDB Parity Verification
    # =========================================================================
    print("\n---------------------------------------------------------------------------")
    print("SCENARIO 4: ChromaDB Persistent Store Filtering Parity")
    print("---------------------------------------------------------------------------")

    chroma_filtered = retrieve(
        query_1,
        k=3,
        collection=chroma_store,
        embedding_service=service,
        metadata_filter=filter_1,
    )
    chroma_hybrid = hybrid_rank(chroma_filtered, keywords=keywords_1)
    show_results("ChromaDB Filtered & Hybrid Results", chroma_hybrid)

    demo_results["scenarios"]["scenario_4_chromadb_parity"] = {
        "query": query_1,
        "filter": filter_1,
        "chroma_filtered_results": chroma_filtered,
        "chroma_hybrid_results": chroma_hybrid,
    }

    # =========================================================================
    # Task 5: Write Sample Filtered-Search Results
    # =========================================================================
    with open(OUTPUT_FILE_PRIMARY, "w", encoding="utf-8") as f:
        json.dump(demo_results, f, indent=2)
    logger.info("Saved primary evaluation output to %s", OUTPUT_FILE_PRIMARY)

    with open(OUTPUT_FILE_DEMO, "w", encoding="utf-8") as f:
        json.dump(demo_results, f, indent=2)
    logger.info("Saved demo summary output to %s", OUTPUT_FILE_DEMO)

    print("\n" + "=" * 75)
    print(f" Demonstration complete. Evaluation results exported to:")
    print(f"  - {OUTPUT_FILE_PRIMARY}")
    print(f"  - {OUTPUT_FILE_DEMO}")
    print("=" * 75 + "\n")

    return demo_results


if __name__ == "__main__":
    run_demonstration()
