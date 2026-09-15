"""Demonstration script for Runtime Document Upload and Dynamic Knowledge-Base Indexing in finee.ai.

Demonstrates:
1. Uploading and indexing Markdown documents at runtime via FastAPI endpoint.
2. Uploading and indexing plain text documents with metadata preservation.
3. Safe rejection of unsupported file formats (HTTP 415) and empty files (HTTP 400).
4. Immediate runtime queryability through the POST /query endpoint without restarting the application.
5. Exporting structured upload and evaluation diagnostics to outputs/evaluations/document_upload_results.json.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.main import app
from src.services.document_upload import get_status_tracker

OUTPUT_DIR = Path("outputs/evaluations")
OUTPUT_FILE = OUTPUT_DIR / "document_upload_results.json"

SAMPLE_UPLOAD_DOCUMENTS = [
    {
        "filename": "financial-advisor-code-of-conduct.md",
        "content_type": "text/markdown",
        "content": (
            "# Financial Advisor Code of Conduct 2026\n\n"
            "## Fiduciary Responsibility\n"
            "Every registered financial advisor must place client financial interests above firm profits.\n"
            "Advisors are strictly prohibited from receiving undisclosed third-party commissions on mutual funds.\n\n"
            "## Annual Suitability Audits\n"
            "Client investment portfolios must undergo formal suitability re-evaluation at least once every 12 months."
        ),
        "expected_status_code": 201,
        "description": "Valid Markdown Document Upload",
    },
    {
        "filename": "client-suitability-guideline.txt",
        "content_type": "text/plain",
        "content": (
            "Client Suitability Guidelines: All high-risk derivatives products require verified prior trading experience "
            "and a signed risk disclosure statement before order execution."
        ),
        "expected_status_code": 201,
        "description": "Valid Plain Text Document Upload",
    },
    {
        "filename": "unauthorized-binary.exe",
        "content_type": "application/x-msdownload",
        "content": "MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00",
        "expected_status_code": 415,
        "description": "Unsupported Executable File (Expected HTTP 415 Rejection)",
    },
    {
        "filename": "empty-notice.txt",
        "content_type": "text/plain",
        "content": "",
        "expected_status_code": 400,
        "description": "Empty Document (Expected HTTP 400 Rejection)",
    },
]

RUNTIME_QUERY_VERIFICATION = {
    "query": "What are the rules regarding undisclosed third-party commissions for financial advisors?",
    "mock_answer": (
        "Under the Financial Advisor Code of Conduct 2026, advisors are strictly prohibited from receiving "
        "undisclosed third-party commissions on mutual funds and must place client interests first [1]."
    ),
}


def run_demonstration() -> Dict[str, Any]:
    """Execute runtime upload and dynamic indexing demonstration."""
    print("=" * 80)
    print("FInee.ai - RUNTIME DOCUMENT UPLOAD & DYNAMIC INDEXING DEMO")
    print("=" * 80)
    print(f"Upload Directory    : {settings.UPLOAD_DIR}")
    print(f"Max Upload Size     : {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.1f} MB")
    print(f"Supported Formats   : {', '.join(settings.SUPPORTED_UPLOAD_EXTENSIONS)}")
    print(f"Vector Collection   : {settings.VECTOR_COLLECTION_NAME}")
    print("-" * 80)

    client = TestClient(app)
    upload_results: List[Dict[str, Any]] = []

    # 1. Test Document Upload Scenarios
    for doc in SAMPLE_UPLOAD_DOCUMENTS:
        filename = doc["filename"]
        content = doc["content"]
        ctype = doc["content_type"]
        expected_code = doc["expected_status_code"]
        desc = doc["description"]

        print(f"\n[UPLOAD TEST] {desc}")
        print(f"  Filename     : {filename}")
        print(f"  Content Type : {ctype}")
        print(f"  Size         : {len(content.encode('utf-8'))} bytes")

        files = {"file": (filename, content.encode("utf-8"), ctype)}
        response = client.post("/documents", files=files)

        status_code = response.status_code
        resp_json = response.json()

        print(f"  HTTP Status  : {status_code} (Expected: {expected_code})")
        if status_code == 201:
            print(f"  Indexing     : SUCCESS (ID: {resp_json.get('document_id')})")
            print(f"  Chunks Added : {resp_json.get('summary', {}).get('chunks_indexed')}")
        else:
            print(f"  Rejection    : {resp_json.get('detail')}")

        upload_results.append({
            "filename": filename,
            "description": desc,
            "status_code": status_code,
            "response": resp_json,
            "success": status_code == expected_code,
        })

    # 2. Dynamic Query Verification (Immediate Runtime Searchability without app restart)
    print("\n" + "=" * 80)
    print("DYNAMIC RUNTIME QUERY VERIFICATION (WITHOUT APP RESTART)")
    print("=" * 80)

    query_text = RUNTIME_QUERY_VERIFICATION["query"]
    mock_answer = RUNTIME_QUERY_VERIFICATION["mock_answer"]

    print(f"Querying Runtime Indexed Knowledge Base:")
    print(f"  Question     : \"{query_text}\"")

    with patch("src.services.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_answer
        query_response = client.post("/query", json={"query": query_text, "k": 3, "min_top_score": 0.5})

    q_status = query_response.status_code
    q_json = query_response.json()

    print(f"  HTTP Status  : {q_status}")
    print(f"  RAG Status   : {q_json.get('status')}")
    print(f"  Answer       : {q_json.get('answer')}")
    print(f"  Citations    : {q_json.get('sources')}")

    # 3. Export structured results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "benchmark": "runtime_document_upload_and_dynamic_indexing",
        "config": {
            "upload_dir": settings.UPLOAD_DIR,
            "max_upload_size_bytes": settings.MAX_UPLOAD_SIZE_BYTES,
            "supported_extensions": settings.SUPPORTED_UPLOAD_EXTENSIONS,
            "vector_collection": settings.VECTOR_COLLECTION_NAME,
        },
        "total_uploads_tested": len(SAMPLE_UPLOAD_DOCUMENTS),
        "upload_records": upload_results,
        "runtime_query_test": {
            "query": query_text,
            "http_status": q_status,
            "rag_status": q_json.get("status"),
            "answer": q_json.get("answer"),
            "sources_count": len(q_json.get("sources", [])),
            "sources": q_json.get("sources", []),
        },
        "tracked_documents_count": len(get_status_tracker().list_all()),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Results successfully exported to: {OUTPUT_FILE}")
    print("=" * 80)

    return summary_payload


if __name__ == "__main__":
    run_demonstration()
