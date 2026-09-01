# FInee.ai — Compliance-Grounded Financial Advisory RAG Platform

## 1. Project Title
**FInee.ai** (Compliance-Grounded Financial Advisory RAG Platform)

---

## 2. Problem Statement
Financial advisory firms maintain an extensive library of market research reports, fund factsheets, regulatory disclosures, and client portfolio documentation. Financial advisors face significant compliance risks when answering client queries because they cannot easily verify answers against the latest approved documents in real-time, risking outdated or non-compliant guidance.

---

## 3. Project Objective
Build a production-grade, secure, compliance-grounded Retrieval-Augmented Generation (RAG) platform that:
- Ingests and processes approved financial documents into semantic chunks and vector embeddings.
- Stores vector representations and compliance metadata in a robust vector database.
- Retrieves high-confidence, approved evidence for advisor questions through semantic search and reranking.
- Generates answers strictly grounded in retrieved evidence with exact source citations.

---

## 4. Current Development Phase
**Phase 1: Foundation & Project Workspace**
- Development environment and scalable workspace setup.
- Configuration management with zero hardcoded secrets.
- Minimal FastAPI application with root (`/`) and health check (`/health`) endpoints.
- Isolated modular architecture ready for future ingestion, embedding, retrieval, and chat components.

---

## 5. Technology Stack
- **Language**: Python 3.11+
- **API Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Configuration & Validation**: [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) & [python-dotenv](https://github.com/theskumar/python-dotenv)
- **Testing**: [pytest](https://docs.pytest.org/) & [httpx](https://www.python-httpx.org/)
- **Future Integration Targets**: OpenAI-compatible LLMs & Embeddings, PostgreSQL with pgvector.

---

## 6. Project Structure

```text
financial-rag-platform/
├── src/
│   ├── __init__.py          # Root package marker
│   ├── api/                 # API routers and endpoints
│   │   ├── __init__.py
│   │   └── routes/          # Modular route definitions
│   │       └── __init__.py
│   ├── core/                # Central config, settings, and infrastructure
│   │   ├── __init__.py
│   │   └── config.py
│   ├── ingestion/           # Document extraction, cleaning, chunking
│   │   └── __init__.py
│   ├── embeddings/          # Vector embedding model integrations
│   │   └── __init__.py
│   ├── retrieval/           # Search, metadata filtering, Top-K, reranking
│   │   └── __init__.py
│   ├── services/            # Business logic connecting modules
│   │   └── __init__.py
│   ├── models/              # Pydantic schemas and data models
│   │   └── __init__.py
│   └── main.py              # FastAPI application entry point
├── data/
│   ├── raw/                 # Original source documents (ignored by git)
│   ├── processed/           # Cleaned/chunked intermediate data (ignored)
│   └── sample/              # Sanitized sample documents for testing
│       └── README.md
├── prompts/                 # System prompts, guardrails, and templates
│   └── README.md
├── outputs/
│   ├── logs/                # Application runtime logs (ignored by git)
│   ├── answers/             # Test answer outputs (ignored by git)
│   └── evaluations/         # Evaluation benchmarks and metrics (ignored)
├── tests/                   # Automated pytest suite
│   ├── __init__.py
│   ├── test_config.py       # Configuration loading tests
│   └── test_main.py         # API endpoint tests
├── scripts/                 # Development and maintenance utilities
│   └── README.md
├── docs/                    # Architectural and technical documentation
│   └── architecture.md
├── .env                     # Local environment variables (ignored by git)
├── .env.example             # Environment variable template (tracked)
├── .gitignore               # Git exclusion rules
├── requirements.txt         # Pinned project dependencies
├── pyproject.toml           # Build system and tool configuration
└── README.md                # Project documentation
```

---

## 7. Folder Responsibilities

| Folder | Purpose |
| :--- | :--- |
| `src/api/` | Future API endpoints and route handlers. |
| `src/core/` | Application configuration, environment settings, and shared utilities. |
| `src/ingestion/` | Document upload, text extraction, cleaning, chunking, and metadata parsing. |
| `src/embeddings/` | Embedding model clients and vectorization operations. |
| `src/retrieval/` | Semantic search, compliance filtering, Top-K retrieval, and reranking. |
| `src/services/` | Business logic orchestrating ingestion, retrieval, and LLM generation. |
| `src/models/` | Domain entities, request/response schemas, and data models. |
| `data/raw/` | Raw financial documents (PDFs, filings, factsheets). |
| `data/processed/` | Processed, extracted, or chunked document datasets. |
| `data/sample/` | Non-confidential sample documents for development and CI testing. |
| `prompts/` | System prompts, compliance instructions, and citation format templates. |
| `outputs/logs/` | Runtime application and ingestion logs. |
| `outputs/answers/` | Generated answer outputs for manual evaluation. |
| `outputs/evaluations/` | Retrieval accuracy metrics and evaluation benchmarks. |
| `tests/` | Automated unit, integration, and regression test suites. |
| `scripts/` | Data migration, bulk ingestion, and maintenance scripts. |
| `docs/` | Architectural diagrams, design documents, and technical guides. |

---

## 8. Environment Setup Instructions

### Step 1: Create Virtual Environment

```bash
# Using Python 3.11+
python3 -m venv .venv
```

### Step 2: Activate Virtual Environment

**macOS / Linux:**
```bash
source .venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create your local `.env` file from `.env.example`:

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows:**
```cmd
copy .env.example .env
```

---

## 9. Running the FastAPI Application

Start the development server with live reload:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Or run directly via python:
```bash
python -m src.main
```

The API will be available at:
- **Base URL**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## 10. API Endpoints

### 1. Root Endpoint
- **Method**: `GET`
- **Path**: `/`
- **Description**: Returns baseline service running status.
- **Example Response**:
  ```json
  {
    "message": "Financial Advisory RAG Platform API is running"
  }
  ```

### 2. Health Check
- **Method**: `GET`
- **Path**: `/health`
- **Description**: Verifies service availability and reports deployment environment.
- **Example Response**:
  ```json
  {
    "status": "healthy",
    "environment": "development"
  }
  ```

---

## 11. Testing & Reproducibility

Run the test suite with pytest:

```bash
pytest -v
```

Execute tests with coverage:
```bash
pytest -v --tb=short
```

---

## 12. Token Counting & Cost Estimation

The token utility uses `tiktoken` with the `cl100k_base` encoding. It counts prompt,
answer, and document tokens, then estimates input and output cost separately using
provider prices per 1,000 tokens. Prices are examples only and should be updated from
the selected provider's current pricing page.

Run the Python-only file estimator:

```bash
python -m scripts.token_cost_estimator prompt.txt answer.txt \
  --input-price 0.0005 --output-price 0.0015
```

It prints JSON containing input tokens, output tokens, each cost, and total cost. The
same functions can be imported from `src.services.token_usage` for RAG cost planning.

Run the three-sample project demonstration and save its results:

```bash
python -m scripts.token_count_demo --output outputs/evaluations/token_count_results.json
```

The demonstration measures a short question, a financial paragraph, and the full
project README. It reports characters, words, tokens, separate input/output costs, and
the combined estimate. The checked-in output is available at
`outputs/evaluations/token_count_results.json`.

### Short Explanation

1. `count_tokens` measures text with the model-compatible tokenizer; tokens are not
  the same as words or characters.
2. `estimate_cost` counts input and output independently because providers bill them
  at different rates.
3. `count_documents` totals a corpus so chunking and retrieval choices can be checked
  before processing thousands of documents.

### Mentor Questions

- Why can token count differ from word count, especially for code or other languages?
- Why should input and output prices be configured separately?
- How do system instructions, retrieved chunks, and chat history affect context limits?
- Why is measuring retrieved context important for both cost and answer quality?
- How would you compare this estimate with the provider's reported usage fields?
- What changes when the provider uses a tokenizer different from `cl100k_base`?

---

## 13. Prompt Templates & Reusable Prompt Design

FInee.ai utilizes centralized prompt templates stored in `prompts/` to decouple prompt definitions, compliance guardrails, and citation rules from application logic.

### Key Benefits
1. **Single Source of Truth**: Grounding rules and citation requirements are edited once and immediately propagate across chat endpoints, batch evaluators, and CLI tools.
2. **Dynamic Runtime Injection**: Named placeholders (`{context}`, `{question}`, etc.) are injected safely at runtime with automatic placeholder validation via `render()`.
3. **Structured & Type-Safe**: Supports both straightforward string templates and `PromptTemplate` objects with explicit variable parsing and error handling.

### Running the Prompt Template Demonstration

```bash
python -m scripts.prompt_template_demo
```

## 13. Token-Aware Chunk Sizing & Overlap

The document ingestion pipeline implements token-aware chunking using `tiktoken` (`cl100k_base` encoding) with sliding token overlap.

### Why Token-Based Sizing & Overlap?
1. **Model Budget Adherence**: LLM context windows and vector embedding limits measure tokens, not characters. Token-based sizing prevents budget overruns on dense text.
2. **Boundary Context Preservation**: Hard splits slice financial conditions and regulatory disclosures across chunk edges. Controlled overlap (default: 60 tokens / 15%) repeats boundary tokens so ideas appear intact in at least one chunk.

### Recommended Settings for FInee.ai:
- **Chunk Size**: `400` tokens (~300 words / 2–3 dense financial paragraphs)
- **Chunk Overlap**: `60` tokens (15% overlap)
- **Top-K Budget**: `5` chunks × `400` tokens = `2,000` tokens of context, well within the 8k context window limit.

### Run the Demonstration:
```bash
python -m scripts.demonstrate_token_chunking --output outputs/evaluations/token_chunking_results.json
```

### Run Tests:
```bash
pytest -v tests/test_token_chunking.py
```

Detailed architectural explanation and trade-off analyses are documented in [`docs/token_chunking.md`](docs/token_chunking.md).

