# FINEE.ai — Knowledge Control System & Grounded Advisory RAG Platform

Enterprise-grade, compliance-grounded Retrieval-Augmented Generation (RAG) platform and Knowledge Control Center for wealth management, financial advisory, and regulatory compliance.

---

## 1. Executive Summary

**FINEE.ai** transforms static compliance policies, regulatory disclosures, fee schedules, and advisory guidelines into an interactive, verifiable, and observable intelligence engine.

- **100% Policy Grounding**: Answers are synthesized strictly from approved vector chunks with exact numeric source citations (`[1]`, `[2]`).
- **Retrieval Guardrails & Safe Refusal**: Pre-LLM relevance scoring rejects insufficient or out-of-domain context with 0 hallucination.
- **Conflicting Evidence Resolution**: Side-by-side comparison of contrasting policy versions (Source A vs Source B) with formal compliance review escalation.
- **Conversational Follow-up Rewriting**: Resolves ambiguous references and pronouns into standalone vector queries while preserving dialogue history.
- **Enterprise Observability**: End-to-end token consumption tracking, cost accounting, advisor monitoring, and cryptographic audit trails.

---

## 2. Platform Architecture

```text
                                  ┌───────────────────────────────┐
                                  │   FINEE.ai Next.js Frontend   │
                                  │    (Dark Enterprise Theme)    │
                                  └───────────────┬───────────────┘
                                                  │ HTTP / JSON (CORS Enabled)
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │   FastAPI Backend Server      │
                                  │       (src.main:app)          │
                                  └───┬───────────┬───────────┬───┘
                                      │           │           │
                     ┌────────────────┴─┐         │         ┌─┴────────────────┐
                     ▼                  ▼         │         ▼                  ▼
             ┌───────────────┐  ┌───────────────┐ │ ┌───────────────┐  ┌───────────────┐
             │  Query Router │  │ Documents API │ │ │  Admin Router │  │ActivityTracker│
             │ (/query)      │  │ (/documents)  │ │ │ (/admin/*)    │  │ (Observability)
             └───────┬───────┘  └───────┬───────┘ │ └───────┬───────┘  └───────┬───────┘
                     │                  │         │         │                  │
                     ▼                  ▼         ▼         ▼                  ▼
    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │                      Ingestion & Core RAG Pipeline Engine                        │
    ├──────────────────────────────────────────────────────────────────────────────────┤
    │ 1. Text Extraction & Cleaning   (src.ingestion.loader & cleaner)                 │
    │ 2. Recursive Semantic Chunking  (src.ingestion.chunking & chunk_metadata)        │
    │ 3. Dense Vector Embeddings      (src.embeddings.embedding_service)               │
    │ 4. ChromaDB Vector Store        (src.retrieval.chroma_store - Cosine HNSW)       │
    │ 5. Candidate Re-ranking         (src.retrieval.reranker)                         │
    │ 6. Retrieval Strength Guardrail (src.services.guardrails)                        │
    │ 7. Query Rewriter & History     (src.services.conversational_rag)                │
    │ 8. Grounded LLM Synthesis       (src.services.llm & context_injection)           │
    └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. UI Experience & Features

### 1. Analysis Session & Advisory (`/chatask`)
- **Client Context Panel**: Switch active entity profiles (Marcus Vance Portfolio, Acme Holdings, Tier 1 Discretionary).
- **Grounded Answer Card**: Direct, synthesized answers with embedded superscript citations.
- **Evidence Used List**: Interactive source cards with relevance scores and click-to-inspect drawers.
- **Conflict Banner & Modal**: Side-by-side Source A vs Source B comparison for divergent provisions.
- **Safe Refusal Banner**: Zero-hallucination refusal state when retrieval confidence is below `0.720`.
- **Right Inspector Panel**: Switch between Ranked Snippets, RAG Pipeline Execution Trace, and Query Audit Trail.

### 2. Knowledge Control Center Overview (`/admin`)
- **KPI Metrics**: Approved Policies (28), Processing (1), Pending Review (3), Archived (2).
- **Ingestion Lifecycle Graphic**: Visual 4-stage pipeline (Raw Ingest -> Chunking -> Embeddings -> ChromaDB).
- **Recent Tracked Documents**: Quick inspection and status overview.
- **Live Audit Trail**: Chronological event stream of system and advisor actions.

### 3. Document Management (`/admin/documents`)
- **Upload Modal**: Drag-and-drop document upload (`.pdf`, `.md`, `.txt`, `.html`) with dynamic indexing.
- **Search & Filters**: Filter by status (`approved`, `processing`, `uploaded`, `review_requested`, `archived`).
- **Document Detail Inspector (`/admin/documents/[id]`)**: Chunk boundary overlays (`Chunk #0`, `Chunk #1`), metadata inspector, lifecycle actions (`Approve`, `Request Review`, `Archive`).

### 4. Knowledge Base Infrastructure (`/admin/knowledge-base`)
- **Telemetry Cards**: Total Policies, Vector Chunks, Cosine Index Health, Retrieval Readiness %.
- **Interactive Test Retrieval Console**: Dry-run queries, adjust Top-K sliders, toggle re-ranking, and inspect real-time candidate scores.
- **Explore Knowledge**: Searchable database of all vector chunks stored in ChromaDB.

### 5. User Monitoring & Token Observability (`/admin/users`)
- **Monitored Personnel**: Advisor profiles with query counts, prompt/completion tokens, cost tracking, and refusal counts.
- **Drill-Down Modal**: Detailed per-user query history and token consumption.

### 6. Audit Trail (`/admin/activity`) & System Settings (`/admin/settings`)
- Filterable system-wide compliance ledger.
- Live view of guardrail parameters (`MIN_TOP_SCORE`, `MIN_SUPPORTING_CHUNKS`, `RETRIEVAL_TOP_K`, models, paths).

---

## 4. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/query` | Guarded similarity search, conversational rewrite, citations, and grounded answer |
| `POST` | `/documents` | Upload, validate, chunk, embed, and dynamically index a compliance document |
| `GET` | `/documents` | List all tracked documents and processing statuses |
| `GET` | `/documents/{id}` | Full document detail with chunk boundary overlays and lifecycle timeline |
| `POST` | `/documents/{id}/approve` | Approve document for production RAG retrieval |
| `POST` | `/documents/{id}/review` | Request formal compliance review for a document |
| `POST` | `/documents/{id}/archive` | Archive document and deprecate from active vector search |
| `GET` | `/admin/overview` | KPI summary statistics, recent documents, and live activity stream |
| `GET` | `/admin/knowledge-base` | Vector infrastructure metrics, pipeline health, and chunk explorer |
| `POST` | `/admin/test-retrieval` | Dry-run retrieval search console with score diagnostics |
| `GET` | `/admin/activity` | System audit trail events log |
| `GET` | `/admin/users` | Monitored users list with token usage and cost accounting |
| `GET` | `/admin/users/{id}/activity` | Granular query history and token breakdown per user |
| `GET` | `/admin/token-usage` | Aggregate token analytics and model distributions |
| `GET` | `/admin/settings` | Active system parameters, guardrail thresholds, and models |

---

## 5. Quick Start & Running Instructions

### Backend Setup & Execution
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run backend test suite (273 tests)
pytest

# 3. Run full integration verification demo
PYTHONPATH=. python scripts/demonstrate_full_frontend_integration.py

# 4. Start FastAPI server on port 8000
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup & Execution
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start Next.js development server (runs on port 3005 by default)
npm run dev

# 4. Open in browser
http://localhost:3005
```
