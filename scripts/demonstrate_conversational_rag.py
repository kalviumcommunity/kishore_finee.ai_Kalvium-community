"""Demonstration script for Conversational RAG and Follow-up Query Rewriting in finee.ai.

Demonstrates:
1. Multi-turn conversation history tracking with bounded rolling turns and token limits.
2. Follow-up query rewriting resolving pronouns and implicit context into standalone retrieval queries.
3. Decoupled pipeline: Rewritten query used strictly for vector retrieval, original question used for answer generation.
4. Preserving original user questions in conversation history (avoiding UI query pollution).
5. Seamless integration with pre-LLM retrieval guardrails and safe refusal for out-of-domain follow-ups.
6. Exporting multi-turn evaluation diagnostics to outputs/evaluations/conversational_rag_results.json.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.services.conversational_rag import (
    ConversationSession,
    conversational_answer,
    format_conversation_history,
    rewrite_followup,
    trim_conversation_history,
)

OUTPUT_DIR = Path("outputs/evaluations")
OUTPUT_FILE = OUTPUT_DIR / "conversational_rag_results.json"

# Multi-turn conversational scenarios simulating realistic user interactions
DEMONSTRATION_TURNS = [
    {
        "turn": 1,
        "type": "Initial Standalone Query",
        "question": "What evidence is required for project submission?",
        "expected_rewrite": "What evidence is required for project submission?",
        "chunks": [
            {
                "rank": 1,
                "score": 0.9520,
                "text": "Project Submission Evidence: All project submissions require three mandatory pieces of evidence: (1) a public GitHub PR link with clean commit history, (2) verified sample terminal output or JSON result artifacts, and (3) a 3-5 minute video explanation demonstrating test execution.",
                "metadata": {
                    "source": "rubric-guidelines.md",
                    "chunk_index": 1,
                    "document_id": "doc_rubric_01",
                },
                "id": "doc_rubric_01:1",
            },
            {
                "rank": 2,
                "score": 0.8910,
                "text": "Submission Verification: Incomplete submissions lacking any of the required evidence items will be returned for revision without evaluation.",
                "metadata": {
                    "source": "submission-policy.pdf",
                    "chunk_index": 0,
                    "document_id": "doc_sub_01",
                },
                "id": "doc_sub_01:0",
            },
        ],
        "mock_answer": "Project submissions require three mandatory evidence items: a public GitHub PR link, verified sample output or test artifacts, and a 3-5 minute video explanation demonstrating execution [1].",
    },
    {
        "turn": 2,
        "type": "Follow-up Query (Pronoun / Topic Elision)",
        "question": "What about the video?",
        "expected_rewrite": "What video explanation is required for project submission?",
        "chunks": [
            {
                "rank": 1,
                "score": 0.9380,
                "text": "Video Explanation Guidelines: The submission video must be 3 to 5 minutes long, include voice narration explaining code changes, and demonstrate all automated test suites passing locally.",
                "metadata": {
                    "source": "video-requirements.md",
                    "chunk_index": 2,
                    "document_id": "doc_video_01",
                },
                "id": "doc_video_01:2",
            },
            {
                "rank": 2,
                "score": 0.8840,
                "text": "Video Hosting: Videos must be uploaded to Loom or YouTube (unlisted) with the shareable link included in the submission form.",
                "metadata": {
                    "source": "video-requirements.md",
                    "chunk_index": 3,
                    "document_id": "doc_video_01",
                },
                "id": "doc_video_01:3",
            },
        ],
        "mock_answer": "The submission video explanation must be 3 to 5 minutes long, feature voice narration covering code changes, and demonstrate all unit test suites passing [1].",
    },
    {
        "turn": 3,
        "type": "Follow-up Query (Context Anchor / Scope Question)",
        "question": "Does it apply to Sprint 2?",
        "expected_rewrite": "Does the video explanation evidence requirement apply to Sprint 2 project submission?",
        "chunks": [
            {
                "rank": 1,
                "score": 0.9240,
                "text": "Sprint 2 Evaluation Scope: Sprint 2 submissions strictly enforce all standard submission evidence requirements, including the PR link, test artifacts, and Loom/YouTube video walkthrough.",
                "metadata": {
                    "source": "sprint-2-syllabus.pdf",
                    "chunk_index": 4,
                    "document_id": "doc_sprint2_01",
                },
                "id": "doc_sprint2_01:4",
            },
            {
                "rank": 2,
                "score": 0.8710,
                "text": "Sprint 2 Deliverables: Evaluation requires 100% test pass rate on retrieval and guardrail modules alongside the recorded demo.",
                "metadata": {
                    "source": "sprint-2-syllabus.pdf",
                    "chunk_index": 5,
                    "document_id": "doc_sprint2_01",
                },
                "id": "doc_sprint2_01:5",
            },
        ],
        "mock_answer": "Yes, Sprint 2 submissions strictly enforce all standard submission evidence requirements, including the PR link, test artifacts, and video walkthrough [1].",
    },
    {
        "turn": 4,
        "type": "Out-of-Domain Follow-up (Guardrail Refusal Trigger)",
        "question": "What is the lunch menu for the Sprint 2 review meeting?",
        "expected_rewrite": "What is the lunch menu for the Sprint 2 review meeting?",
        "chunks": [
            {
                "rank": 1,
                "score": 0.4850,
                "text": "Facility Notice: Cafeteria operates Monday through Friday from 11:30 AM to 2:00 PM on the 2nd floor.",
                "metadata": {
                    "source": "building-services.txt",
                    "chunk_index": 0,
                    "document_id": "doc_fac_01",
                },
                "id": "doc_fac_01:0",
            },
            {
                "rank": 2,
                "score": 0.3920,
                "text": "Visitor Guidelines: External guests must register at security.",
                "metadata": {
                    "source": "visitor-policy.md",
                    "chunk_index": 0,
                    "document_id": "doc_vis_01",
                },
                "id": "doc_vis_01:0",
            },
        ],
        "mock_answer": None,  # Should refuse without calling LLM
    },
]


async def run_demonstration() -> Dict[str, Any]:
    """Execute the multi-turn conversational RAG demonstration."""
    print("=" * 80)
    print("FInee.ai - CONVERSATIONAL RAG & FOLLOW-UP QUERY REWRITING DEMO")
    print("=" * 80)
    print(f"Max History Turns  : {settings.MAX_CONVERSATION_TURNS}")
    print(f"Max History Tokens : {settings.MAX_HISTORY_TOKENS}")
    print(f"Guardrail Min Score: {settings.MIN_TOP_SCORE}")
    print(f"Retrieval Top-K    : {settings.RETRIEVAL_TOP_K}")
    print("-" * 80)

    session = ConversationSession()
    evaluation_records: List[Dict[str, Any]] = []

    for turn_info in DEMONSTRATION_TURNS:
        turn_num = turn_info["turn"]
        turn_type = turn_info["type"]
        question = turn_info["question"]
        chunks = turn_info["chunks"]
        mock_ans = turn_info["mock_answer"]

        print(f"\n[TURN {turn_num}] ({turn_type})")
        print(f"User Question         : \"{question}\"")

        # Capture history state prior to processing this turn
        pre_turn_history = session.history
        if pre_turn_history:
            print("Conversation Context  :")
            for msg in pre_turn_history:
                print(f"  {msg['role'].capitalize()}: {msg['content'][:90]}...")
        else:
            print("Conversation Context  : [Initial Turn - No History]")

        # Execute conversational turn
        if mock_ans:
            with patch("src.services.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_ans
                result = await session.ask(question=question, chunks=chunks)
        else:
            result = await session.ask(question=question, chunks=chunks)

        rewritten = result["rewritten_query"]
        status = result["status"]
        answer = result["answer"]
        sources = result["sources"]

        print(f"Rewritten Query       : \"{rewritten}\"")
        print(f"Retrieval Top Score   : {chunks[0]['score']:.4f}")
        print(f"Guardrail Status      : {status}")
        print(f"Answer Generated      : {answer}")
        print(f"Citations Returned    : {sources if sources else '[]'}")
        print(f"Session History Length: {len(session.history)} messages ({len(session.history) // 2} turns)")

        record = {
            "turn": turn_num,
            "turn_type": turn_type,
            "original_question": question,
            "rewritten_query": rewritten,
            "top_chunk_score": chunks[0]["score"],
            "status": status,
            "answer": answer,
            "sources": sources,
            "history_length_messages": len(session.history),
        }
        evaluation_records.append(record)

    # Save output to JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "benchmark": "conversational_rag_query_rewriting",
        "config": {
            "max_conversation_turns": settings.MAX_CONVERSATION_TURNS,
            "max_history_tokens": settings.MAX_HISTORY_TOKENS,
            "min_top_score": settings.MIN_TOP_SCORE,
            "retrieval_top_k": settings.RETRIEVAL_TOP_K,
        },
        "total_turns_tested": len(DEMONSTRATION_TURNS),
        "turns": evaluation_records,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Results successfully exported to: {OUTPUT_FILE}")
    print("=" * 80)

    return summary_payload


if __name__ == "__main__":
    asyncio.run(run_demonstration())
