# Streaming Responses & Citation Display

## Overview

This module implements progressive answer streaming and source citation display for the FInee.ai compliance-grounded RAG service.

Rather than forcing users to wait silently while retrieval, prompt assembly, and token generation complete, answers are streamed progressively over Server-Sent Events (SSE). Simultaneously, structured source evidence citations (such as `[1]`) are delivered alongside the response, allowing users to verify claims against the underlying compliance document chunks.

---

## Key Architecture & Features

### 1. Server-Sent Events (SSE) Protocol (`POST /query/stream`)
The backend exposes a streaming endpoint using FastAPI's `StreamingResponse`. The client consumes standard SSE text data formatted as JSON events:

```
data: {"type": "citations", "sources": [...]}

data: {"type": "token", "text": "An "}

data: {"type": "token", "text": "expense "}

data: {"type": "done"}
```

#### Event Schema:
- **`citations`**: Emitted immediately after context retrieval. Contains source metadata, citation markers (`[1]`), document titles, chunk IDs, sections, similarity scores, and full chunk text.
- **`token`**: Emitted progressively as the LLM generates response tokens.
- **`done`**: Signals successful stream completion.
- **`error`**: Emitted if an interruption, network error, or backend failure occurs (`{"type": "error", "message": "..."}`).

---

### 2. Interactive Web Chat Interface (`/ui`)

The Web Chat UI (`src/api/ui.py`) is rendered directly at `/` and `/ui`. Key features include:
- **Progressive Token Appending**: Updates the answer box dynamically as tokens arrive.
- **Citation Badges (`[1]`, `[2]`)**: Highlighted inline citation tags linking claims to retrieved sources.
- **Expandable Source Details**: Accessible `<details>` and `<summary>` components that allow users to inspect retrieved chunk text upon clicking a citation.
- **Resilient Error Recovery**: Captures stream failures, preserves any partial text/citations already received, displays a clear error alert banner, and offers a **Retry** button.

---

## Code Implementation Details

- **Pipeline Streaming Generator**: `src/rag/rag_pipeline.py` (`rag_pipeline_stream`)
- **FastAPI Endpoints**: `src/api/rag_api.py` (`POST /query/stream`, `GET /ui`)
- **Frontend Template**: `src/api/ui.py` (`HTML_CHAT_UI`)
- **Demonstration Script**: `scripts/demonstrate_streaming_rag.py`
- **Evaluation Output Artifact**: `outputs/evaluations/streaming_rag_demo.json`
- **Automated Test Suite**: `tests/test_streaming_rag.py`

---

## Verification & Evaluation Results

All unit and integration tests passed cleanly:
```bash
.venv\Scripts\python.exe -m pytest tests/test_streaming_rag.py -v
```
Output:
- `test_rag_pipeline_stream_success`: PASSED
- `test_rag_pipeline_stream_error_handling`: PASSED
- `test_rag_pipeline_stream_empty_query`: PASSED
- `test_stream_query_endpoint`: PASSED
- `test_stream_query_endpoint_error_handling`: PASSED
- `test_chat_ui_endpoint`: PASSED

Demonstration script execution output:
```bash
.venv\Scripts\python.exe scripts/demonstrate_streaming_rag.py
```
Outputs saved to `outputs/evaluations/streaming_rag_demo.json`.
