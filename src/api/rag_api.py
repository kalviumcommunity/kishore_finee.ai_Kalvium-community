"""FastAPI backend for the FInee.ai RAG service."""

import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.rag.source_citation import answer_with_citations
from src.rag.rag_pipeline import rag_pipeline_stream
from src.api.ui import HTML_CHAT_UI


app = FastAPI(
    title="FInee.ai RAG API",
    description="Backend API for the FInee.ai RAG service with progressive streaming & citations",
    version="1.0.0"
)


# ---------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000
    )


class Source(BaseModel):
    source: str
    chunk_id: str | None = None
    chunk_index: int | None = None
    score: float | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    status: str


# ---------------------------------------------------------
# Web UI Endpoints
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def get_chat_ui():
    """Serve the interactive RAG Chat & Citation interface."""
    return HTMLResponse(content=HTML_CHAT_UI)


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    """Check whether the RAG API is running."""

    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# RAG query endpoint (Non-Streaming)
# ---------------------------------------------------------

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """Accept a question and return a RAG answer with sources."""

    try:
        result = answer_with_citations(
            request.question,
            k=2
        )

        sources = []

        for citation, details in result.get(
            "citations",
            {}
        ).items():

            sources.append({
                "source": details.get("source"),
                "chunk_id": details.get("chunk_id"),
                "chunk_index": details.get("chunk_index"),
                "score": details.get("score")
            })

        return {
            "answer": result.get(
                "answer",
                "I don't have enough information in the provided context."
            ),
            "sources": sources,
            "status": "answered"
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="RAG service failed"
        )


# ---------------------------------------------------------
# Progressive Streaming Query Endpoint
# ---------------------------------------------------------

@app.post("/query/stream")
async def stream_query(request: QueryRequest):
    """Stream a RAG answer progressively with citations via Server-Sent Events (SSE)."""

    async def events():
        try:
            async for event in rag_pipeline_stream(request.question):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            error_event = {
                "type": "error",
                "message": "The answer stopped streaming. Please retry."
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")