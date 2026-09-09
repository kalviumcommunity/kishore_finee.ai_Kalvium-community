"""End-to-end RAG pipeline for FInee.ai."""

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