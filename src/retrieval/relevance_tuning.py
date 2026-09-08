"""Retrieval relevance tuning for FInee.ai."""

from src.embeddings.similarity import cosine_similarity


# ---------------------------------------------------------
# Test queries
# ---------------------------------------------------------

test_queries = [
    {
        "query": "Mutual funds and investment",
        "expected_source": "sample-fund.md"
    },
    {
        "query": "How do equity funds invest?",
        "expected_source": "sample-equity.md"
    },
    {
        "query": "How do interest rates affect debt funds?",
        "expected_source": "sample-debt.md"
    },
    {
        "query": "What is an expense ratio?",
        "expected_source": "sample-expenses.md"
    }
]


# ---------------------------------------------------------
# Sample embeddings
# Same 3-dimensional format used in similarity.py
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
    "Mutual funds and investment": [0.90, 0.80, 0.10],
    "How do equity funds invest?": [0.72, 0.76, 0.18],
    "How do interest rates affect debt funds?": [0.20, 0.30, 0.88],
    "What is an expense ratio?": [0.30, 0.20, 0.90]
}


# ---------------------------------------------------------
# Retrieval
# ---------------------------------------------------------

def retrieve(query, k=3, min_score=0.0, metadata_filter=None):
    """Retrieve the top-k relevant chunks."""

    query_embedding = query_embeddings[query]

    results = []

    for record in chunk_records:

        # Metadata filtering
        if metadata_filter:
            matches = all(
                record["metadata"].get(key) == value
                for key, value in metadata_filter.items()
            )

            if not matches:
                continue

        score = cosine_similarity(
            query_embedding,
            record["embedding"]
        )

        if score >= min_score:
            results.append({
                **record,
                "score": float(score)
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:k]


# ---------------------------------------------------------
# Retrieval evaluation
# ---------------------------------------------------------

def evaluate(setting):
    """Evaluate one retrieval configuration."""

    rows = []

    for item in test_queries:

        results = retrieve(
            item["query"],
            k=setting["k"],
            min_score=setting["min_score"],
            metadata_filter=setting["filter"]
        )

        sources = [
            result["metadata"]["source"]
            for result in results
        ]

        hit = item["expected_source"] in sources

        rows.append({
            "query": item["query"],
            "expected_source": item["expected_source"],
            "returned_sources": sources,
            "hit": hit
        })

    return rows


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("FInee.ai - RETRIEVAL RELEVANCE TUNING")
    print("=" * 60)

    settings = [
        {
            "name": "baseline_k2",
            "k": 2,
            "filter": None,
            "min_score": 0.0
        },
        {
            "name": "baseline_k3",
            "k": 3,
            "filter": None,
            "min_score": 0.0
        },
        {
            "name": "strict_k3",
            "k": 3,
            "filter": None,
            "min_score": 0.70
        }
    ]

    summary = []

    # -----------------------------------------------------
    # Evaluate every setting
    # -----------------------------------------------------

    for setting in settings:

        rows = evaluate(setting)

        hits = sum(
            1
            for row in rows
            if row["hit"]
        )

        hit_rate = hits / len(rows)

        summary.append({
            "setting": setting["name"],
            "hit_rate": hit_rate,
            "details": rows
        })

    # -----------------------------------------------------
    # Print detailed results
    # -----------------------------------------------------

    print("\nTEST RESULTS")
    print("-" * 60)

    for result in summary:

        print(
            f"\nSetting: {result['setting']}"
        )

        print(
            f"Hit rate: "
            f"{result['hit_rate']:.2%}"
        )

        for row in result["details"]:

            status = "PASS" if row["hit"] else "FAIL"

            print(f"\n  {status}")
            print(f"  Query: {row['query']}")
            print(
                f"  Expected: "
                f"{row['expected_source']}"
            )
            print(
                f"  Returned: "
                f"{row['returned_sources']}"
            )

    # -----------------------------------------------------
    # Select best setting
    # -----------------------------------------------------

    best = max(
        summary,
        key=lambda item: item["hit_rate"]
    )

    print("\n" + "=" * 60)
    print("BEST RETRIEVAL SETTING")
    print("=" * 60)

    print(
        f"Setting : {best['setting']}"
    )

    print(
        f"Hit rate: {best['hit_rate']:.2%}"
    )

    print("\nReason:")
    print(
        "The selected setting provides the highest "
        "retrieval hit rate on the test queries."
    )

    print("=" * 60)


if __name__ == "__main__":
    main()