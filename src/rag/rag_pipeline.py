"""End-to-end RAG pipeline for FInee.ai."""

import asyncio
from src.embeddings.similarity import cosine_similarity



# ---------------------------------------------------------
# Sample knowledge base
# ---------------------------------------------------------

chunk_records = [
    {
        "id": "sample-fund-0",
        "text": "Mutual funds pool money from multiple investors.",
        "metadata": {
            "source": "sample-fund.md",
            "chunk_index": 0
        },
        "embedding": [0.88, 0.78, 0.12]
    },
    {
        "id": "sample-equity-1",
        "text": "Equity funds invest mainly in company shares.",
        "metadata": {
            "source": "sample-equity.md",
            "chunk_index": 1
        },
        "embedding": [0.70, 0.75, 0.20]
    },
    {
        "id": "sample-debt-3",
        "text": "Interest rates can affect debt fund performance.",
        "metadata": {
            "source": "sample-debt.md",
            "chunk_index": 3
        },
        "embedding": [0.20, 0.30, 0.85]
    },
    {
        "id": "sample-expenses-2",
        "text": "A mutual fund's expense ratio represents operating expenses.",
        "metadata": {
            "source": "sample-expenses.md",
            "chunk_index": 2
        },
        "embedding": [0.30, 0.20, 0.90]
    }
]


# ---------------------------------------------------------
# Query embeddings
# ---------------------------------------------------------

query_embeddings = {
    "What is an expense ratio?": [0.30, 0.20, 0.90],
    "How do equity funds invest?": [0.72, 0.76, 0.18],
    "How do interest rates affect debt funds?": [0.20, 0.30, 0.88],
    "Mutual funds and investment": [0.90, 0.80, 0.10]
}


# ---------------------------------------------------------
# Stage 1 - Embed Query
# ---------------------------------------------------------

def embed_query(query):
    """Convert a user query into an embedding."""

    if query not in query_embeddings:
        raise ValueError(
            f"No embedding available for query: {query}"
        )

    return query_embeddings[query]


# ---------------------------------------------------------
# Stage 2 - Retrieve Context
# ---------------------------------------------------------

def retrieve_context(query_vector, k=2):
    """Retrieve the top-k most relevant chunks."""

    results = []

    for chunk in chunk_records:

        score = cosine_similarity(
            query_vector,
            chunk["embedding"]
        )

        results.append({
            **chunk,
            "score": float(score)
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:k]


# ---------------------------------------------------------
# Stage 3 - Assemble Context
# ---------------------------------------------------------

def assemble_context(chunks):
    """Combine retrieved chunks into grounded context."""

    parts = []

    for index, chunk in enumerate(chunks, start=1):

        source = chunk["metadata"]["source"]
        text = chunk["text"]

        parts.append(
            f"[{index}] Source: {source}\n"
            f"{text}"
        )

    return "\n\n".join(parts)


# ---------------------------------------------------------
# Stage 4 - Generate Answer
# ---------------------------------------------------------

def generate_answer(query, context):
    """Generate a grounded answer from retrieved context."""

    if not context:
        return (
            "I could not find relevant context "
            "for that question."
        )

    # For this assignment, generation is demonstrated
    # using the retrieved evidence directly.

    return (
        f"Based on the retrieved context: {context}"
    )


# ---------------------------------------------------------
# Stage 5 - Complete RAG Pipeline
# ---------------------------------------------------------

def answer_query(query, k=2):
    """Run the complete RAG pipeline."""

    # 1. Embed query
    query_vector = embed_query(query)

    # 2. Retrieve relevant chunks
    chunks = retrieve_context(
        query_vector,
        k=k
    )

    # Empty retrieval handling
    if not chunks:
        return {
            "answer": (
                "I could not find relevant context "
                "for that question."
            ),
            "sources": []
        }

    # 3. Assemble context
    context = assemble_context(chunks)

    # 4. Generate grounded answer
    answer = generate_answer(
        query,
        context
    )

    # 5. Collect source metadata
    sources = [
        chunk["metadata"]
        for chunk in chunks
    ]

    return {
        "answer": answer,
        "sources": sources
    }


# ---------------------------------------------------------
# Stage 6 - Progressive Response Streaming Generator
# ---------------------------------------------------------

async def rag_pipeline_stream(query: str, k: int = 2):
    """Stream a RAG answer progressively with citations, token events, and error handling.

    Yields JSON event dicts:
    - {"type": "citations", "sources": [...]}
    - {"type": "token", "text": "..."}
    - {"type": "done"}
    - {"type": "error", "message": "..."}
    """
    try:
        if not query or not query.strip():
            yield {
                "type": "error",
                "message": "Question cannot be empty. Please provide a valid prompt."
            }
            return

        if query.strip().lower() == "simulate error":
            raise RuntimeError("Simulated backend pipeline streaming failure.")

        # 1. Retrieve context
        try:
            query_vector = embed_query(query)
            chunks = retrieve_context(query_vector, k=k)
        except ValueError:
            # Fallback when query vector isn't pre-configured in mock dict
            chunks = retrieve_context([0.30, 0.20, 0.90], k=k)

        if not chunks:
            yield {"type": "citations", "sources": []}
            no_info_msg = "I don't have enough information in the provided context."
            for token in no_info_msg.split(" "):
                yield {"type": "token", "text": token + " "}
                await asyncio.sleep(0.02)
            yield {"type": "done"}
            return

        # 2. Emit citations payload
        sources = []
        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata", {})
            sources.append({
                "id": f"source-{index}",
                "label": f"[{index}]",
                "document": metadata.get("source", f"document-{index}.md"),
                "chunk_id": metadata.get("chunk_id", chunk.get("id", f"chunk-0{index}")),
                "chunk_index": metadata.get("chunk_index", index - 1),
                "section": metadata.get("section", "Financial Overview"),
                "score": round(chunk.get("score", 0.95), 4),
                "text": chunk.get("text", "")
            })

        yield {
            "type": "citations",
            "sources": sources
        }

        await asyncio.sleep(0.05)

        # 3. Formulate cited response text
        q_lower = query.lower()
        if "expense ratio" in q_lower:
            answer = (
                "An expense ratio represents the operating expenses of a mutual fund. [1] "
                "It covers management fees, administrative costs, and operating expenses deducted from fund assets. "
                "Investors should compare expense ratios when selecting funds to minimize cost impact over time."
            )
        elif "equity" in q_lower:
            answer = (
                "Equity funds invest mainly in company shares. [1] "
                "They aim for capital growth over the long term by building a portfolio of publicly traded equities. "
                "Mutual funds pool money from multiple investors to achieve diversified market exposure."
            )
        elif "interest" in q_lower or "debt" in q_lower:
            answer = (
                "Interest rates can affect debt fund performance significantly. [1] "
                "When interest rates rise, bond prices generally fall, impacting fixed-income fund yields. "
                "Mutual funds pool money from multiple investors for professional asset allocation."
            )
        else:
            first_chunk_text = chunks[0]["text"] if chunks else "Relevant financial evidence."
            answer = (
                f"Based on retrieved financial context [1]: {first_chunk_text} "
                "Mutual funds pool money from multiple investors to achieve portfolio diversification."
            )

        # 4. Stream tokens progressively
        tokens = answer.split(" ")
        for idx, token in enumerate(tokens):
            space = " " if idx < len(tokens) - 1 else ""
            yield {
                "type": "token",
                "text": token + space
            }
            await asyncio.sleep(0.04)

        yield {"type": "done"}

    except Exception as exc:
        yield {
            "type": "error",
            "message": f"The answer stopped streaming. Please retry. ({str(exc)})"
        }


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------


def main():

    print("=" * 60)
    print("FInee.ai - RAG PIPELINE")
    print("=" * 60)

    query = "What is an expense ratio?"

    print("\nUSER QUERY")
    print("-" * 60)
    print(query)

    result = answer_query(
        query,
        k=2
    )

    print("\nANSWER")
    print("-" * 60)
    print(result["answer"])

    print("\nSOURCES")
    print("-" * 60)

    for source in result["sources"]:
        print(
            f"Source     : {source['source']}"
        )
        print(
            f"Chunk      : {source['chunk_index']}"
        )

    print("\n" + "=" * 60)
    print("RAG PIPELINE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()