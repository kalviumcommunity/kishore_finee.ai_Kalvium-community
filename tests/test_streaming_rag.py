"""Tests for streaming RAG responses and citation display API."""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient

from src.api.rag_api import app
from src.rag.rag_pipeline import rag_pipeline_stream


client = TestClient(app)


# ---------------------------------------------------------
# Test Stage 1 - Unit Tests for Streaming Generator
# ---------------------------------------------------------

def test_rag_pipeline_stream_success():
    """Test that rag_pipeline_stream yields citations, tokens, and done events."""
    async def _run():
        events = []
        async for event in rag_pipeline_stream("What is an expense ratio?", k=2):
            events.append(event)
        return events

    events = asyncio.run(_run())

    assert len(events) >= 3
    
    # 1. Citations event
    citations_event = events[0]
    assert citations_event["type"] == "citations"
    assert "sources" in citations_event
    assert len(citations_event["sources"]) > 0

    first_source = citations_event["sources"][0]
    assert "id" in first_source
    assert "label" in first_source
    assert "document" in first_source
    assert "chunk_id" in first_source
    assert "text" in first_source
    assert first_source["label"] == "[1]"

    # 2. Token events
    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) > 0
    reconstructed_answer = "".join(e["text"] for e in token_events)
    assert "expense ratio" in reconstructed_answer.lower()
    assert "[1]" in reconstructed_answer

    # 3. Done event
    assert events[-1]["type"] == "done"


def test_rag_pipeline_stream_error_handling():
    """Test that pipeline errors yield a structured error event."""
    async def _run():
        events = []
        async for event in rag_pipeline_stream("Simulate Error"):
            events.append(event)
        return events

    events = asyncio.run(_run())

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "message" in events[0]
    assert "Please retry" in events[0]["message"] or "failure" in events[0]["message"].lower()


def test_rag_pipeline_stream_empty_query():
    """Test that empty queries return an error event."""
    async def _run():
        events = []
        async for event in rag_pipeline_stream("   "):
            events.append(event)
        return events

    events = asyncio.run(_run())

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "Question cannot be empty" in events[0]["message"]



# ---------------------------------------------------------
# Test Stage 2 - Integration Tests for FastAPI API Endpoint
# ---------------------------------------------------------

def test_stream_query_endpoint():
    """Test POST /query/stream SSE endpoint."""
    response = client.post(
        "/query/stream",
        json={"question": "What is an expense ratio?"}
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    lines = response.text.strip().split("\n\n")
    parsed_events = []

    for line in lines:
        if line.startswith("data: "):
            event_json = json.loads(line[6:])
            parsed_events.append(event_json)

    assert len(parsed_events) >= 3
    event_types = [e["type"] for e in parsed_events]
    assert "citations" in event_types
    assert "token" in event_types
    assert "done" in event_types


def test_stream_query_endpoint_error_handling():
    """Test POST /query/stream handles pipeline errors gracefully."""
    response = client.post(
        "/query/stream",
        json={"question": "Simulate Error"}
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    lines = response.text.strip().split("\n\n")
    parsed_events = [json.loads(line[6:]) for line in lines if line.startswith("data: ")]

    assert len(parsed_events) == 1
    assert parsed_events[0]["type"] == "error"
    assert "Please retry" in parsed_events[0]["message"] or "failure" in parsed_events[0]["message"].lower()


def test_chat_ui_endpoint():
    """Test GET / and GET /ui serve the HTML Chat interface."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "text/html" in res_root.headers.get("content-type", "")
    assert "Streaming Responses & Citation Display" in res_root.text

    res_ui = client.get("/ui")
    assert res_ui.status_code == 200
    assert "Streaming Responses & Citation Display" in res_ui.text
