"""Demonstration script for Streaming Responses & Citation Display for FInee.ai RAG."""

import asyncio
import json
import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.rag.rag_pipeline import rag_pipeline_stream


async def demonstrate_streaming():
    print("=" * 70)
    print("FInee.ai - STREAMING RESPONSES & CITATION DISPLAY DEMONSTRATION")
    print("=" * 70)

    queries = [
        "What is an expense ratio?",
        "How do equity funds invest?",
        "Simulate Error"
    ]

    demo_results = []

    for query_idx, query in enumerate(queries, start=1):
        print(f"\n[{query_idx}/{len(queries)}] USER QUERY: \"{query}\"")
        print("-" * 70)

        received_citations = []
        accumulated_answer = ""
        stream_events = []
        is_error = False
        error_msg = None

        start_time = time.time()

        async for event in rag_pipeline_stream(query, k=2):
            event_type = event.get("type")
            stream_events.append(event)

            if event_type == "citations":
                received_citations = event.get("sources", [])
                print(f"[CITATIONS RECEIVED]: {len(received_citations)} source chunk(s) attached.")
                for src in received_citations:
                    print(f"   * {src['label']} Document: {src['document']} (Chunk ID: {src['chunk_id']}, Score: {src['score']})")
                print(" -> [ANSWER STREAMING]: ", end="", flush=True)

            elif event_type == "token":
                token_text = event.get("text", "")
                accumulated_answer += token_text
                print(token_text, end="", flush=True)
                await asyncio.sleep(0.02)

            elif event_type == "error":
                is_error = True
                error_msg = event.get("message")
                print(f"\n[STREAM ERROR]: {error_msg}")

            elif event_type == "done":
                elapsed = round(time.time() - start_time, 3)
                print(f"\n[STREAM COMPLETED]: Finished in {elapsed} seconds.")

        demo_results.append({
            "query_index": query_idx,
            "question": query,
            "citations": received_citations,
            "answer": accumulated_answer,
            "is_error": is_error,
            "error_message": error_msg,
            "events_count": len(stream_events),
            "status": "error" if is_error else "completed"
        })

    # Save output evaluation artifact
    output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs", "evaluations")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "streaming_rag_demo.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "title": "FInee.ai Streaming RAG & Citation Demonstration",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_queries_tested": len(queries),
            "results": demo_results
        }, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Artifact saved successfully to: {output_path}")
    print("=" * 70)


def main():
    asyncio.run(demonstrate_streaming())


if __name__ == "__main__":
    main()
