# Runtime Document Upload & Dynamic Knowledge-Base Indexing in FInee.ai

This document describes the design, architecture, validation safeguards, ingestion workflow, and API endpoints for runtime document upload and dynamic knowledge-base indexing in the `finee.ai` compliance-grounded financial advisory RAG platform.

---

## 1. Overview & Architecture

The runtime document upload system enables authorized users and compliance administrators to expand the knowledge base dynamically without requiring application restarts or vector database re-indexing:

```
Client (curl / Frontend)
     │
     │  POST /documents (multipart/form-data)
     ▼
[ 1. Extension & Size Validation ]  ──(Unsupported / Oversized)──→  HTTP 415 / 413 Error
     │
     ▼
[ 2. Safe Storage Layer ]
     │  • Path traversal sanitization
     │  • Collision-safe stored filename (doc_xxx_filename)
     │  • Streaming buffer to prevent memory exhaustion
     ▼
[ 3. Unified Ingestion Pipeline ]
     │  • Text Extraction (pypdf, txt, md, bs4)
     │  • Text Cleaning (Mojibake, NFKC, header/footer strip)
     │  • Token-Aware Chunking (recursive chunking)
     │  • Compliance Metadata Tagging (source, doc_id, timestamp)
     ▼
[ 4. Embedding Generation ]
     │  • Batch embedding (text-embedding-3-small)
     ▼
[ 5. Dynamic Vector Store Indexing ]
     │  • Direct upsert into active ChromaDB collection
     ▼
[ 6. Immediate Query Availability ]  ──→  Searchable via POST /query
```

---

## 2. API Endpoints

### 2.1. Upload Document (`POST /documents`)

Accepts a single document file, validates its format and size, executes the ingestion pipeline, and indexes the resulting chunks into the active vector store.

- **URL**: `/documents`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Status Code**: `201 Created`

#### Sample Request:

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@financial-advisor-code-of-conduct.md"
```

#### Successful Response:

```json
{
  "status": "indexed",
  "document_id": "doc_90659ef24c94",
  "filename": "financial-advisor-code-of-conduct.md",
  "summary": {
    "chunks_created": 2,
    "chunks_indexed": 2
  }
}
```

---

### 2.2. List Tracked Documents (`GET /documents`)

Returns a list of all documents uploaded during the runtime session along with their processing status and chunk statistics.

- **URL**: `/documents`
- **Method**: `GET`
- **Status Code**: `200 OK`

#### Sample Response:

```json
[
  {
    "document_id": "doc_90659ef24c94",
    "original_filename": "financial-advisor-code-of-conduct.md",
    "stored_filename": "doc_90659ef24c94_financial-advisor-code-of-conduct.md",
    "upload_timestamp": "2026-09-09T09:44:09.123456+00:00",
    "status": "indexed",
    "error_message": null,
    "chunks_created": 2,
    "chunks_indexed": 2,
    "file_size_bytes": 482,
    "content_type": "text/markdown",
    "completed_at": "2026-09-09T09:44:09.456789+00:00"
  }
]
```

---

### 2.3. Query Active Knowledge Base (`POST /query`)

Queries the indexed knowledge base with retrieval guardrails and grounded citation generation.

- **URL**: `/query`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Status Code**: `200 OK`

#### Sample Request:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the rules regarding undisclosed third-party commissions for financial advisors?",
    "k": 3
  }'
```

#### Sample Response:

```json
{
  "answer": "Under the Financial Advisor Code of Conduct 2026, advisors are strictly prohibited from receiving undisclosed third-party commissions on mutual funds and must place client interests first [1].",
  "sources": [
    {
      "marker": "[1]",
      "source": "financial-advisor-code-of-conduct.md",
      "chunk_index": 0,
      "metadata": {
        "source": "financial-advisor-code-of-conduct.md",
        "document_id": "doc_90659ef24c94",
        "chunk_index": 0,
        "approval_status": "approved",
        "upload_timestamp": "2026-09-09T09:44:09.123456+00:00"
      },
      "id": "doc_90659ef24c94:0"
    }
  ],
  "status": "answered",
  "refusal_reason": null,
  "metrics": {
    "top_score": 0.942,
    "supporting_chunks_count": 1,
    "retrieved_chunks_count": 3,
    "llm_called": true
  },
  "question": "What are the rules regarding undisclosed third-party commissions for financial advisors?"
}
```

---

## 3. Supported Formats & Validation Safeguards

| Format | Extension | Extraction Engine | MIME Types |
| :--- | :--- | :--- | :--- |
| **Markdown** | `.md` | UTF-8 Text Decoder with header extraction | `text/markdown`, `text/plain` |
| **Plain Text** | `.txt` | UTF-8 Text Decoder with error tolerance | `text/plain` |
| **PDF Document** | `.pdf` | `pypdf.PdfReader` with page splitting | `application/pdf` |
| **HTML Document**| `.html`, `.htm` | `BeautifulSoup` text parser | `text/html` |

### Validation Safeguards:
1. **Extension Normalization**: Extensions are converted to lowercase and matched against `SUPPORTED_UPLOAD_EXTENSIONS`.
2. **Unsupported Types Rejected (HTTP 415)**: Executables (`.exe`), scripts (`.sh`, `.py`, `.js`), archives (`.zip`, `.tar`), and binary formats are rejected immediately before disk writes.
3. **Empty File Rejection (HTTP 400)**: Files with 0 bytes are rejected.
4. **File Size Enforcement (HTTP 413)**: Uploads exceeding `MAX_UPLOAD_SIZE_BYTES` (default: 10 MB) are terminated mid-stream, and partial bytes are removed from disk.
5. **Path Traversal Prevention**: Filenames containing `../`, `..\`, null bytes, or absolute paths are sanitized using `sanitize_filename()`, strictly scoping storage to the configured `UPLOAD_DIR`.

---

## 4. Ingestion Pipeline Reuse

To preserve data consistency across the platform, the runtime upload pipeline reuses the **exact same core modules** as the initial batch corpus ingestion:

1. **Text Extraction**: Calls `src.ingestion.document_loader.load_text()`.
2. **Text Cleaning**: Calls `src.ingestion.text_cleaner.clean_text()` (NFKC normalization, Mojibake repair, repetitive header/footer suppression).
3. **Token Chunking**: Calls `src.ingestion.chunking.recursive_chunks()`.
4. **Metadata Tagging**: Calls `src.ingestion.chunk_metadata.create_chunk()` to attach provenance metadata.
5. **Embedding**: Calls `src.embeddings.embedding_service.EmbeddingService.embed_chunks()`.
6. **Vector Indexing**: Calls `src.vector_store.service.VectorStoreService.upsert_records()` and `src.retrieval.chroma_store.ChromaVectorStore.add_records()`.

---

## 5. Metadata & Citation Preservation

Newly indexed chunks preserve complete regulatory metadata:

```json
{
  "source": "financial-advisor-code-of-conduct.md",
  "document_id": "doc_90659ef24c94",
  "document_version": "1.0",
  "chunk_index": 0,
  "effective_date": "2026-09-09",
  "approval_status": "approved",
  "upload_timestamp": "2026-09-09T09:44:09.123456+00:00",
  "embedding_model": "text-embedding-3-small"
}
```

This guarantees that answers generated from uploaded documents produce standard citation markers (`[1] doc#chunk`) identical to pre-indexed documents.

---

## 6. Duplicate Handling & Collision Prevention

1. **Storage Level**: Every uploaded file is assigned a unique `document_id` prefix (e.g. `doc_90659ef24c94_policy.md`), preventing file collisions even if users upload identically named files.
2. **Vector Database Level**: Chunk IDs are deterministically keyed by `f"{document_id}:{chunk_index}"`. Re-uploading a revised document version updates or adds chunks cleanly without corrupting existing records.

---

## 7. Error Handling & HTTP Status Codes

| Error Condition | HTTP Code | Error Response Sample |
| :--- | :---: | :--- |
| **Unsupported Extension** | `415` | `{"detail": "Unsupported file type: '.exe'. Supported extensions: .htm, .html, .md, .pdf, .txt"}` |
| **File Exceeds Max Size** | `413` | `{"detail": "File size exceeds maximum limit of 10.0 MB."}` |
| **Empty File (0 bytes)** | `400` | `{"detail": "Uploaded file 'empty.txt' is empty (0 bytes)."}` |
| **Empty Extracted Text** | `400` | `{"detail": "No extractable text found in 'blank.pdf'."}` |
| **Missing Filename** | `400` / `422` | `{"detail": "Filename is required and cannot be empty."}` |
| **Vector DB / API Failure** | `500` | `{"detail": "Internal server error during document indexing."}` |

---

## 8. Future Roadmap: Asynchronous Processing & Task Queues

For high-throughput enterprise deployments with 100+ page documents:
1. **Background Job Queues**: Transitioning from synchronous HTTP processing to Celery/Redis workers with async job tickets (`POST /documents` $\to$ `202 Accepted` with `task_id`).
2. **Real-Time Progress Tracking**: WebSocket or Server-Sent Events (SSE) emitting progress stages (`extraction: 25%`, `embedding: 80%`, `indexed: 100%`).
3. **Chunk Batch Throttling**: Rate-limited embedding API calls with automatic retry backoff for large multi-document batches.
