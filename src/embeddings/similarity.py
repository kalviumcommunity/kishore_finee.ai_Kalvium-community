"""Embedding similarity and distance metrics for FInee.ai."""

from numpy import dot
from numpy.linalg import norm


def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    denominator = norm(a) * norm(b)

    if denominator == 0:
        return 0.0

    return dot(a, b) / denominator


def rank_chunks(query_embedding, chunk_records):
    """Rank chunks by cosine similarity to the query."""
    ranked = []

    for record in chunk_records:
        score = cosine_similarity(
            query_embedding,
            record["embedding"]
        )

        ranked.append({
            **record,
            "score": float(score)
        })

    return sorted(
        ranked,
        key=lambda item: item["score"],
        reverse=True
    )


def main():
    """Demonstrate cosine similarity and chunk ranking."""

    # Example embeddings representing document meanings.
    query_embedding = [0.90, 0.80, 0.10]

    chunk_records = [
        {
            "text": "Mutual funds pool money from multiple investors.",
            "metadata": {
                "source": "sample-fund.md",
                "chunk_index": 0
            },
            "embedding": [0.88, 0.78, 0.12]
        },
        {
            "text": "Equity funds invest mainly in company shares.",
            "metadata": {
                "source": "sample-equity.md",
                "chunk_index": 1
            },
            "embedding": [0.70, 0.75, 0.20]
        },
        {
            "text": "A mutual fund's expense ratio represents operating expenses.",
            "metadata": {
                "source": "sample-expenses.md",
                "chunk_index": 2
            },
            "embedding": [0.30, 0.20, 0.90]
        },
        {
            "text": "Interest rates can affect debt fund performance.",
            "metadata": {
                "source": "sample-debt.md",
                "chunk_index": 3
            },
            "embedding": [0.20, 0.30, 0.85]
        }
    ]

    ranked = rank_chunks(
        query_embedding,
        chunk_records
    )

    print("=" * 60)
    print("FInee.ai - EMBEDDING SIMILARITY")
    print("=" * 60)

    print("\nQuery:")
    print("Mutual funds and investment")

    print("\nRanked chunks:")
    print("-" * 60)

    for index, record in enumerate(ranked, start=1):
        print(f"\nRank {index}")
        print(f"Similarity : {record['score']:.4f}")
        print(f"Source     : {record['metadata']['source']}")
        print(f"Chunk      : {record['metadata']['chunk_index']}")
        print(f"Text       : {record['text']}")

    print("\n" + "=" * 60)
    print("MOST SIMILAR")
    print("=" * 60)

    print(ranked[0]["text"])
    print(f"Similarity: {ranked[0]['score']:.4f}")

    print("\n" + "=" * 60)
    print("LEAST SIMILAR")
    print("=" * 60)

    print(ranked[-1]["text"])
    print(f"Similarity: {ranked[-1]['score']:.4f}")


if __name__ == "__main__":
    main()