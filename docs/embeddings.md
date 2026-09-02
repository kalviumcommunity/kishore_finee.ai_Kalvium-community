# Embedding Generation Pipeline

This document details the embedding generation architecture implemented for the `finee.ai` compliance-grounded financial advisory RAG platform.

---

## 1. Pipeline Architecture

The embedding stage transforms cleaned document chunks into dense semantic vector representations via an OpenAI-compatible Embeddings API:

```
DOCUMENT
   ↓
EXTRACTION
   ↓
CLEANING
   ↓
CHUNK CREATION (Text + Metadata)
   ↓
EMBEDDING SERVICE (Batching & Retries)
   ↓
OPENAI-COMPATIBLE EMBEDDINGS API
   ↓
VECTOR VALIDATION
   ↓
STRUCTURED RECORD (Vector + Text + Metadata)
   ↓
READY FOR VECTOR DATABASE
```

---

## 2. Why Vectors Cannot Be Stored Alone

In production financial RAG systems, storing vector arrays in isolation creates critical failure points:
- **Loss of Provenance & Context**: A 1536-dimensional array of floats cannot be reversed into human-readable text. Storing vectors without their source text prevents the system from displaying evidence or sending context to the LLM.
- **Auditability & Citations**: Financial advisory requires exact citations (document source, version, page, section, effective date, and approval status). When vectors are decoupled from metadata, citation generation becomes impossible.
- **Payload Integrity**: Vector databases store embeddings alongside the payload (`text` and `metadata`). Generating this composite structure early ensures clean handoffs to the storage layer.

---

## 3. The "Same Model" Rule

> [!IMPORTANT]
> **Document chunks and user queries MUST be embedded using the exact same model.**

```
Document Chunk
      ↓
text-embedding-3-small
      ↓
Document Vector (1536-dim)  ──────┐
                                  ├──> Cosine Similarity Comparison
Query Text                        │
      ↓                           │
text-embedding-3-small            │
      ↓                           │
Query Vector (1536-dim)     ──────┘
```

If document chunks are embedded with `text-embedding-3-small` while a query is embedded with a different model (e.g. `text-embedding-ada-002` or `all-MiniLM-L6-v2`), the vectors will exist in completely different coordinate spaces. Semantic search will return meaningless, degenerate similarity scores.

To enforce this, `finee.ai` centralizes embedding model configuration in `src.core.config.settings.EMBEDDING_MODEL` and exposes unified `embed_chunks` and `embed_query` functions.

---

## 4. Batch Embedding & Performance

Sending individual API requests per chunk introduces severe latency and network overhead. The embedding service batches chunk texts:
- **Configurable Batch Size**: Configured via `EMBEDDING_BATCH_SIZE` (default: 50 chunks per batch).
- **Index Preservation**: Strict 1-to-1 index matching ensures that vector $i$ returned by the API always attaches to chunk $i$, even if API responses arrive out of order.
- **Re-run Safety**: Chunks that already have an embedding matching the configured model are automatically preserved and skipped during re-ingestion runs.

---

## 5. Embedding Record Structure

Every generated record produces the following structure:

```json
{
    "text": "Marcus paid the advisory fee on 20 August.",
    "metadata": {
        "source": "client-payment-record.pdf",
        "document_id": "doc_001",
        "document_version": "1.0",
        "chunk_index": 12,
        "page": 2,
        "section": "Payment History",
        "char_start": 1450,
        "char_end": 1494,
        "effective_date": "2026-08-20",
        "approval_status": "approved"
    },
    "embedding": [0.0241, -0.0812, 0.0523, "...1536 dimensions..."],
    "embedding_model": "text-embedding-3-small",
    "created_at": "2026-09-02T14:50:00+00:00"
}
```

---

## 6. Error Handling & Retries

- **Transient Errors (Rate Limits 429, 5xx Server Errors, Connection Timeouts)**: Automatically retried using exponential backoff (e.g., $0.5\text{s} \to 1.0\text{s} \to 2.0\text{s}$, up to `max_retries`).
- **Permanent Errors (401 Authentication, 400 Bad Request)**: Raised immediately as `EmbeddingAPIError` or `EmbeddingConfigError` without indefinite retries.
- **Batch Failure Isolation**: Identifies the exact batch index that failed if unrecoverable.
- **Validation**: Enforces non-empty float vectors of uniform dimensionality prior to returning.
