# Vector Database Setup & Insert/Readback Verification

This document details the vector database integration for the `finee.ai` compliance-grounded financial advisory RAG platform.

---

## 1. Why a Vector Database Is Needed

Dense semantic retrieval requires indexing and persisting mathematical vector representations produced by the embedding model:
- **Persistent Storage**: Avoids expensive re-embedding of document chunks across application restarts.
- **Index Management**: Provides optimized indexing structures (e.g. HNSW graphs) for similarity comparisons.
- **Co-Location of Context & Provenance**: Vector databases store embeddings alongside chunk text and compliance metadata, enabling full auditability and source attribution.

---

## 2. Why the Collection Dimension Must Match the Embedding Model

An embedding model projects text into a fixed coordinate space of dimension $D$ (e.g., $1536$ dimensions for `text-embedding-3-small`).
- If a collection expects $1536$ dimensions but receives vectors with $768$ dimensions, vector operations will fail immediately with dimension mismatch errors.
- Vector indices allocate fixed memory layouts based on the declared dimension.
- The `VectorStoreService` validates every incoming vector prior to insertion and rejects any mismatched vectors with `DimensionMismatchError`.

---

## 3. Why Cosine Distance Is Used

Cosine similarity measures the angle between vectors rather than Euclidean distance (magnitude):
$$\text{Cosine Distance} = 1 - \text{Cosine Similarity} = 1 - \frac{A \cdot B}{\|A\| \times \|B\|}$$

- **Length Invariance**: Document chunks and short search queries may differ in word count, but cosine distance focuses purely on semantic direction rather than token frequency magnitude.
- In Chroma, this is configured via the collection metadata `{"hnsw:space": "cosine"}`.

---

## 4. Co-Location of Vector, Text, and Metadata

Storing raw vectors alone is insufficient in financial RAG. Every record co-locates:
- **Stable ID**: Deterministic identifier formatted as `document_id:chunk_index`.
- **Vector**: 1536-dimensional float array.
- **Original Text**: Preserved verbatim for prompt context augmentation and evidence display.
- **Compliance Metadata**: Source file, document version, page number, section name, approval status, and effective dates.

```json
{
  "id": "account-guide.md:0",
  "vector": [0.0241, -0.0812, 0.0523, "..."],
  "text": "Marcus paid the advisory fee on 20 August. The transaction was verified.",
  "metadata": {
    "source": "account-guide.md",
    "document_id": "account-guide.md",
    "document_version": "1.0",
    "chunk_index": 0,
    "page": 2,
    "section": "Payment History",
    "approval_status": "approved",
    "embedding_model": "text-embedding-3-small"
  }
}
```

---

## 5. Configuration Settings

Vector storage settings are managed via `src.core.config.settings` and loaded from environment variables (`.env`):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `VECTOR_DB_TYPE` | `chroma` | Vector database engine type (`chroma`, `memory`) |
| `VECTOR_COLLECTION_NAME` | `rag_chunks` | Default target collection name |
| `VECTOR_DIMENSION` | `1536` | Expected vector dimensionality |
| `VECTOR_DISTANCE_METRIC` | `cosine` | Distance metric (`cosine`, `l2`, `ip`) |
| `VECTOR_DB_PATH` | `./data/vector_db` | Local directory for database persistence |

---

## 6. How to Run Insert & Readback Verification

To execute the verification routine via CLI:
```bash
python -m src.vector_store.service
```

To run the automated unit tests:
```bash
pytest tests/test_vector_store.py -v
```

---

## 7. Verification Report Output Example

```text
Vector Store Verification
=========================
Collection: rag_chunks
Dimension: 1536
Metric: cosine

Inserted ID: account-guide.md:0
Readback ID: account-guide.md:0
Vector length: 1536
Text preserved: PASS
Metadata preserved: PASS
Dimension valid: PASS
Readback successful: PASS
```
