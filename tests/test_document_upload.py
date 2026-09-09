"""Comprehensive unit and integration tests for Runtime Document Upload and Dynamic Indexing."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from src.core.config import settings
from src.main import app
from src.retrieval.chroma_store import ChromaVectorStore
from src.services.document_upload import (
    ChunkingError,
    DocumentRecord,
    DocumentStatus,
    DocumentStatusTracker,
    DocumentUploadError,
    EmptyDocumentError,
    EmptyFileError,
    ExtractionError,
    FileOversizedError,
    IndexingError,
    InvalidFilenameError,
    UnsupportedFileTypeError,
    get_status_tracker,
    process_uploaded_document,
    sanitize_filename,
    store_upload,
    validate_file_extension,
)
from src.vector_store.service import VectorStoreService, get_vector_store


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_status_tracker():
    """Ensure status tracker is cleared between test runs."""
    tracker = get_status_tracker()
    tracker.clear()
    yield
    tracker.clear()


# ============================================================================
# 1. Validation & Sanitization Unit Tests
# ============================================================================

def test_validate_file_extension_supported():
    """Verify supported extensions are correctly recognized and normalized."""
    assert validate_file_extension("policy.txt") == ".txt"
    assert validate_file_extension("GUIDELINES.MD") == ".md"
    assert validate_file_extension("report.PDF") == ".pdf"
    assert validate_file_extension("terms.html") == ".html"
    assert validate_file_extension("disclosure.HTM") == ".htm"


def test_validate_file_extension_unsupported():
    """Verify unsupported extensions raise UnsupportedFileTypeError."""
    with pytest.raises(UnsupportedFileTypeError) as exc:
        validate_file_extension("executable.exe")
    assert "Unsupported file type: '.exe'" in str(exc.value)

    with pytest.raises(UnsupportedFileTypeError):
        validate_file_extension("script.py")

    with pytest.raises(UnsupportedFileTypeError):
        validate_file_extension("data.csv")


def test_validate_file_extension_missing():
    """Verify missing extension raises UnsupportedFileTypeError."""
    with pytest.raises(UnsupportedFileTypeError):
        validate_file_extension("no_extension_file")


def test_validate_file_extension_empty():
    """Verify empty or None filename raises InvalidFilenameError."""
    with pytest.raises(InvalidFilenameError):
        validate_file_extension("")
    with pytest.raises(InvalidFilenameError):
        validate_file_extension("   ")


def test_sanitize_filename_traversal():
    """Verify directory traversal patterns are stripped safely."""
    assert sanitize_filename("../../etc/passwd.md") == "passwd.md"
    assert sanitize_filename("..\\..\\windows\\system32.txt") == "system32.txt"
    assert sanitize_filename("folder/subfolder/file.pdf") == "file.pdf"


def test_sanitize_filename_special_chars():
    """Verify prohibited characters and null bytes are sanitized."""
    sanitized = sanitize_filename("my<cool>:doc|file?.txt")
    assert "<" not in sanitized
    assert ":" not in sanitized
    assert "|" not in sanitized
    assert "?" not in sanitized
    assert sanitized.endswith(".txt")


# ============================================================================
# 2. Safe Storage Unit Tests
# ============================================================================

@pytest.mark.anyio
async def test_store_upload_success(tmp_path: Path):
    """Verify valid file upload is safely stored with metadata."""
    file_bytes = b"# Compliance Policy\n\nAll advisors must record client suitability assessments."
    upload_file = MagicMock()
    upload_file.filename = "suitability-policy.md"
    upload_file.content_type = "text/markdown"
    upload_file.read = AsyncMock(side_effect=[file_bytes, b""])

    meta = await store_upload(file=upload_file, upload_dir=tmp_path)

    assert meta["original_filename"] == "suitability-policy.md"
    assert meta["file_size_bytes"] == len(file_bytes)
    assert Path(meta["stored_path"]).exists()
    assert Path(meta["stored_path"]).read_bytes() == file_bytes

    # Check status tracker registration
    rec = get_status_tracker().get(meta["document_id"])
    assert rec is not None
    assert rec.status == DocumentStatus.UPLOADED
    assert rec.original_filename == "suitability-policy.md"


@pytest.mark.anyio
async def test_store_upload_empty_file(tmp_path: Path):
    """Verify empty file upload (0 bytes) is rejected with EmptyFileError."""
    upload_file = MagicMock()
    upload_file.filename = "empty.txt"
    upload_file.content_type = "text/plain"
    upload_file.read = AsyncMock(return_value=b"")

    with pytest.raises(EmptyFileError):
        await store_upload(file=upload_file, upload_dir=tmp_path)


@pytest.mark.anyio
async def test_store_upload_oversized_file(tmp_path: Path):
    """Verify oversized file exceeding max_size_bytes is rejected with FileOversizedError."""
    large_bytes = b"x" * 1024  # 1 KB
    upload_file = MagicMock()
    upload_file.filename = "large.txt"
    upload_file.content_type = "text/plain"
    upload_file.read = AsyncMock(side_effect=[large_bytes, b""])

    # Limit to 500 bytes
    with pytest.raises(FileOversizedError):
        await store_upload(file=upload_file, upload_dir=tmp_path, max_size_bytes=500)


@pytest.mark.anyio
async def test_store_upload_duplicate_filename_no_collision(tmp_path: Path):
    """Verify multiple uploads of the same filename produce distinct stored files."""
    file_bytes1 = b"Content Version 1"
    file_bytes2 = b"Content Version 2"

    upload_file1 = MagicMock()
    upload_file1.filename = "policy.md"
    upload_file1.read = AsyncMock(side_effect=[file_bytes1, b""])

    upload_file2 = MagicMock()
    upload_file2.filename = "policy.md"
    upload_file2.read = AsyncMock(side_effect=[file_bytes2, b""])

    meta1 = await store_upload(file=upload_file1, upload_dir=tmp_path)
    meta2 = await store_upload(file=upload_file2, upload_dir=tmp_path)

    assert meta1["document_id"] != meta2["document_id"]
    assert meta1["stored_filename"] != meta2["stored_filename"]
    assert Path(meta1["stored_path"]).exists()
    assert Path(meta2["stored_path"]).exists()


# ============================================================================
# 3. Ingestion & Dynamic Indexing Unit Tests
# ============================================================================

@pytest.mark.anyio
async def test_process_uploaded_document_txt(tmp_path: Path):
    """Verify end-to-end ingestion and indexing of a .txt document."""
    txt_file = tmp_path / "kyc-guidelines.txt"
    txt_file.write_text(
        "KYC Verification Requirements: All client identities must be verified "
        "using government-issued photo ID and proof of address before onboarding.",
        encoding="utf-8",
    )

    vector_store = VectorStoreService(in_memory=True, collection_name="test_upload_txt")

    result = await process_uploaded_document(
        path=txt_file,
        document_id="doc_kyc_01",
        original_filename="kyc-guidelines.txt",
        vector_store=vector_store,
    )

    assert result["status"] == "indexed"
    assert result["document_id"] == "doc_kyc_01"
    assert result["filename"] == "kyc-guidelines.txt"
    assert result["summary"]["chunks_created"] >= 1
    assert result["summary"]["chunks_indexed"] >= 1

    # Verify vector store contents
    rec = vector_store.get_record_by_id("doc_kyc_01:0", collection_name="test_upload_txt")
    assert rec is not None
    assert "KYC Verification Requirements" in rec["text"]
    assert rec["metadata"]["source"] == "kyc-guidelines.txt"
    assert rec["metadata"]["document_id"] == "doc_kyc_01"
    assert rec["metadata"]["chunk_index"] == 0
    assert "upload_timestamp" in rec["metadata"]


@pytest.mark.anyio
async def test_process_uploaded_document_md(tmp_path: Path):
    """Verify end-to-end ingestion and indexing of a Markdown document with multiple sections."""
    md_file = tmp_path / "fee_schedule.md"
    md_file.write_text(
        "# Advisory Fee Schedule\n\n"
        "## Management Fees\n"
        "The standard advisory fee is 0.85% of AUM billed quarterly.\n\n"
        "## Performance Fees\n"
        "High-watermark accounts incur a 10% performance fee on annual excess return.",
        encoding="utf-8",
    )

    vector_store = VectorStoreService(in_memory=True, collection_name="test_upload_md")

    result = await process_uploaded_document(
        path=md_file,
        document_id="doc_fee_99",
        original_filename="fee_schedule.md",
        vector_store=vector_store,
    )

    assert result["status"] == "indexed"
    assert result["summary"]["chunks_created"] >= 1
    assert vector_store.count(collection_name="test_upload_md") >= 1


@pytest.mark.anyio
async def test_process_uploaded_document_empty_text_error(tmp_path: Path):
    """Verify document with blank content raises EmptyDocumentError."""
    blank_file = tmp_path / "blank.txt"
    blank_file.write_text("   \n\n   \t  ", encoding="utf-8")

    with pytest.raises(EmptyDocumentError):
        await process_uploaded_document(
            path=blank_file,
            document_id="doc_blank_01",
            original_filename="blank.txt",
        )

    # Status tracker should reflect failed status
    rec = get_status_tracker().get("doc_blank_01")
    assert rec is not None
    assert rec.status == DocumentStatus.FAILED
    assert rec.error_message is not None


@pytest.mark.anyio
async def test_process_uploaded_document_extraction_failure(tmp_path: Path):
    """Verify extraction failure marks document as failed and raises ExtractionError."""
    non_existent = tmp_path / "missing.txt"

    with pytest.raises(ExtractionError):
        await process_uploaded_document(
            path=non_existent,
            document_id="doc_missing",
            original_filename="missing.txt",
        )

    rec = get_status_tracker().get("doc_missing")
    assert rec is not None
    assert rec.status == DocumentStatus.FAILED


# ============================================================================
# 4. FastAPI Endpoint Integration Tests (POST /documents)
# ============================================================================

def test_api_upload_txt_success(client: TestClient, tmp_path: Path):
    """Verify POST /documents successfully indexes a .txt document."""
    file_content = b"Financial Ombudsman Process: Disputes unresolved within 8 weeks escalate to the Ombudsman."
    files = {"file": ("ombudsman-rules.txt", file_content, "text/plain")}

    response = client.post("/documents", files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "indexed"
    assert data["filename"] == "ombudsman-rules.txt"
    assert data["summary"]["chunks_created"] >= 1
    assert data["summary"]["chunks_indexed"] >= 1

    # Verify document status endpoint
    doc_id = data["document_id"]
    status_resp = client.get(f"/documents/{doc_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "indexed"
    assert status_data["document_id"] == doc_id


def test_api_upload_md_success(client: TestClient):
    """Verify POST /documents successfully indexes a .md document."""
    file_content = b"# Anti-Money Laundering\n\nSuspicious transaction reports must be filed within 24 hours."
    files = {"file": ("aml-policy.md", file_content, "text/markdown")}

    response = client.post("/documents", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "indexed"
    assert data["filename"] == "aml-policy.md"


def test_api_upload_unsupported_extension_415(client: TestClient):
    """Verify POST /documents rejects unsupported file extensions with HTTP 415."""
    file_content = b"echo 'malicious script'"
    files = {"file": ("script.sh", file_content, "application/x-sh")}

    response = client.post("/documents", files=files)
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_api_upload_empty_file_400(client: TestClient):
    """Verify POST /documents rejects empty files (0 bytes) with HTTP 400."""
    files = {"file": ("empty.txt", b"", "text/plain")}

    response = client.post("/documents", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_upload_missing_filename_400(client: TestClient):
    """Verify POST /documents rejects missing filename with HTTP 400 or 422."""
    files = {"file": ("", b"Some text content", "text/plain")}

    response = client.post("/documents", files=files)
    assert response.status_code in (400, 422)


def test_api_list_documents(client: TestClient):
    """Verify GET /documents returns list of tracked documents."""
    file_content = b"Tax Compliance Notice: Foreign accounts must be reported annually under FATCA."
    files = {"file": ("fatca-notice.txt", file_content, "text/plain")}

    client.post("/documents", files=files)

    response = client.get("/documents")
    assert response.status_code == 200
    records = response.json()
    assert len(records) >= 1
    assert any(r["original_filename"] == "fatca-notice.txt" for r in records)


def test_api_get_document_status_not_found(client: TestClient):
    """Verify GET /documents/{doc_id} returns 404 for non-existent document ID."""
    response = client.get("/documents/non_existent_doc_id_999")
    assert response.status_code == 404


# ============================================================================
# 5. Runtime Searchability & /query Integration Tests
# ============================================================================

def test_api_runtime_indexing_and_query_integration(client: TestClient):
    """Integration test: Upload document at runtime and immediately query without application restart."""
    doc_text = (
        "Project Submission Rubric 2026: Submissions require a public GitHub PR link, "
        "verified sample terminal output artifacts, and a 3-5 minute video explanation."
    )
    files = {"file": ("project-submission-rubric.txt", doc_text.encode("utf-8"), "text/plain")}

    # 1. Upload and index document at runtime
    upload_res = client.post("/documents", files=files)
    assert upload_res.status_code == 201
    assert upload_res.json()["status"] == "indexed"

    # 2. Query knowledge base immediately through POST /query without restart
    with patch("src.services.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Submissions require a GitHub PR link, sample terminal output, and a video explanation [1]."

        query_payload = {
            "query": "What evidence is required for project submission in the 2026 rubric?",
            "k": 3,
        }
        query_res = client.post("/query", json=query_payload)

        assert query_res.status_code == 200
        q_data = query_res.json()
        assert q_data["status"] == "answered"
        assert len(q_data["sources"]) >= 1
        assert "project-submission-rubric.txt" in q_data["sources"][0]["source"]


def test_api_query_empty_bad_request(client: TestClient):
    """Verify POST /query returns HTTP 400 when query string is empty."""
    response = client.post("/query", json={"query": "   "})
    assert response.status_code == 400
