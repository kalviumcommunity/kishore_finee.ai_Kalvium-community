"""FastAPI backend for the FInee.ai RAG service."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.rag.source_citation import answer_with_citations


app = FastAPI(
    title="FInee.ai RAG API",
    description="Backend API for the FInee.ai RAG service",
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
# Health endpoint
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    """Check whether the RAG API is running."""

    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# RAG query endpoint
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