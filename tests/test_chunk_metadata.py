"""Unit tests for chunk metadata and source tracking."""

import pytest
from src.ingestion.chunk_metadata import (
    create_chunk,
    create_chunk_metadata,
    find_char_positions,
    get_source_reference,
    attach_metadata_to_chunks,
    Chunk,
    ChunkMetadata,
)
from src.ingestion.chunking import chunk_document_with_metadata



def test_every_chunk_has_metadata():
    chunk = create_chunk(
        text="Sample financial advisory advice.",
        source="advisory-guidelines.pdf",
    )
    assert "text" in chunk
    assert "metadata" in chunk
    assert isinstance(chunk["metadata"], dict)


def test_source_is_present():
    chunk = create_chunk(
        text="Sample text",
        source="client-payment-record.pdf",
    )
    assert chunk["metadata"]["source"] == "client-payment-record.pdf"

    # Verify source is mandatory
    with pytest.raises(ValueError):
        create_chunk(text="Sample text", source="")

    with pytest.raises(ValueError):
        create_chunk(text="Sample text", source=None)


def test_document_id_is_preserved():
    chunk = create_chunk(
        text="Sample text",
        source="doc.pdf",
        document_id="doc_001",
    )
    assert chunk["metadata"]["document_id"] == "doc_001"


def test_document_version_is_preserved():
    chunk = create_chunk(
        text="Sample text",
        source="doc.pdf",
        document_version="3.2",
    )
    assert chunk["metadata"]["document_version"] == "3.2"


def test_chunk_index_is_correct():
    chunk = create_chunk(
        text="Sample text",
        source="doc.pdf",
        chunk_index=12,
    )
    assert chunk["metadata"]["chunk_index"] == 12


def test_page_is_preserved_when_available():
    chunk = create_chunk(
        text="Sample text",
        source="doc.pdf",
        page=2,
    )
    assert chunk["metadata"]["page"] == 2


def test_section_is_preserved_when_available():
    chunk = create_chunk(
        text="Sample text",
        source="doc.pdf",
        section="Payment History",
    )
    assert chunk["metadata"]["section"] == "Payment History"


def test_char_start_and_char_end_are_preserved():
    chunk = create_chunk(
        text="Marcus paid the fee.",
        source="doc.pdf",
        char_start=1450,
        char_end=1470,
    )
    assert chunk["metadata"]["char_start"] == 1450
    assert chunk["metadata"]["char_end"] == 1470


def test_effective_date_is_preserved():
    chunk = create_chunk(
        text="Sample text",
        source="doc.pdf",
        effective_date="2026-08-20",
    )
    assert chunk["metadata"]["effective_date"] == "2026-08-20"


def test_approval_status_is_preserved():
    for status in ["draft", "processing", "pending_approval", "approved", "superseded", "archived"]:
        chunk = create_chunk(
            text="Sample text",
            source="doc.pdf",
            approval_status=status,
        )
        assert chunk["metadata"]["approval_status"] == status


def test_missing_optional_metadata_becomes_none():
    chunk = create_chunk(
        text="Sample text",
        source="doc.txt",
    )
    metadata = chunk["metadata"]
    assert metadata["source"] == "doc.txt"
    assert metadata["chunk_index"] == 0
    assert metadata["document_id"] is None
    assert metadata["document_version"] is None
    assert metadata["page"] is None
    assert metadata["section"] is None
    assert metadata["char_start"] is None
    assert metadata["char_end"] is None
    assert metadata["effective_date"] is None
    assert metadata["approval_status"] is None


def test_multiple_chunks_receive_unique_chunk_indexes():
    raw_chunks = ["First chunk.", "Second chunk.", "Third chunk."]
    full_text = "First chunk. Second chunk. Third chunk."
    chunks = attach_metadata_to_chunks(
        chunks=raw_chunks,
        source="report.pdf",
        document_id="doc_100",
        document_version="1.0",
        full_text=full_text,
    )
    assert len(chunks) == 3
    indexes = [c["metadata"]["chunk_index"] for c in chunks]
    assert indexes == [0, 1, 2]

    # Verify char_start and char_end
    assert chunks[0]["metadata"]["char_start"] == 0
    assert chunks[0]["metadata"]["char_end"] == len("First chunk.")
    assert chunks[1]["metadata"]["char_start"] == full_text.find("Second chunk.")


def test_source_traceability_returns_correct_information():
    chunk = create_chunk(
        text="Marcus paid the advisory fee on 20 August.",
        source="Client Payment Record",
        document_version="1.0",
        chunk_index=12,
        page=2,
        section="Payment History",
        approval_status="approved",
        effective_date="2026-08-20",
    )
    ref = get_source_reference(chunk)

    assert "Client Payment Record" in ref
    assert "1.0" in ref
    assert "2" in ref
    assert "Payment History" in ref
    assert "12" in ref
    assert "approved" in ref
    assert "2026-08-20" in ref


def test_chunk_document_with_metadata_integration():
    text = "Marcus paid the advisory fee. The payment was completed on 20 August."
    chunks = chunk_document_with_metadata(
        text=text,
        source="client-record.pdf",
        strategy="sentence",
        document_id="doc_005",
        document_version="2.1",
        approval_status="approved",
    )
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["metadata"]["source"] == "client-record.pdf"
        assert chunk["metadata"]["document_id"] == "doc_005"
        assert chunk["metadata"]["document_version"] == "2.1"
        assert chunk["metadata"]["approval_status"] == "approved"
        assert chunk["metadata"]["char_start"] is not None
        assert chunk["metadata"]["char_end"] is not None


def test_find_char_positions_and_create_chunk_metadata():
    text = "Intro paragraph. Body paragraph. Conclusion paragraph."
    chunks = ["Intro paragraph.", "Body paragraph.", "Conclusion paragraph."]
    positions = find_char_positions(text, chunks)

    assert positions == [0, 17, 33]

    docs = create_chunk_metadata("sample.txt", chunks, positions)
    assert len(docs) == 3
    assert docs[0]["metadata"]["source"] == "sample.txt"
    assert docs[0]["metadata"]["chunk_index"] == 0
    assert docs[0]["metadata"]["char_start"] == 0
    assert docs[0]["metadata"]["char_end"] == 16
    assert docs[1]["metadata"]["chunk_index"] == 1
    assert docs[1]["metadata"]["char_start"] == 17

