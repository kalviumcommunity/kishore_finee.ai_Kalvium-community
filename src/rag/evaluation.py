"""RAG evaluation and answer quality scoring for FInee.ai."""

from src.rag.source_citation import answer_with_citations


# ---------------------------------------------------------
# Test set
# ---------------------------------------------------------

test_set = [
    {
        "question": "What is an expense ratio?",
        "expected_points": [
            "expense ratio",
            "operating expenses",
            "mutual fund"
        ],
        "expected_sources": {"sample-expenses.md"}
    },
    {
        "question": "How do interest rates affect debt funds?",
        "expected_points": [
            "interest rates",
            "debt fund performance"
        ],
        "expected_sources": {"sample-debt.md"}
    },
    {
        "question": "How do equity funds invest?",
        "expected_points": [
            "equity funds",
            "company shares"
        ],
        "expected_sources": {"sample-equity.md"}
    }
]


# ---------------------------------------------------------
# Correctness scoring
# ---------------------------------------------------------

def judge_expected_points(answer, expected_points):
    """Score whether expected answer points appear in the answer."""

    answer_lower = answer.lower()

    matched = 0

    for point in expected_points:
        if point.lower() in answer_lower:
            matched += 1

    if not expected_points:
        return 0.0

    return matched / len(expected_points)


# ---------------------------------------------------------
# Grounding scoring
# ---------------------------------------------------------

def judge_grounding(answer, citations):
    """Check whether cited answer content is supported by retrieved chunks."""

    if not citations:
        return 0.0

    answer_lower = answer.lower()

    supported_claims = 0
    total_claims = 0

    # Remove citation markers and evaluate factual text.
    for citation, details in citations.items():
        if citation in answer:
            total_claims += 1

            source_text = details["text"].lower()

            # Check whether important words from the cited source
            # are represented in the answer.
            source_words = set(source_text.split())
            answer_words = set(answer_lower.split())

            overlap = source_words.intersection(answer_words)

            if len(overlap) >= 3:
                supported_claims += 1

    if total_claims == 0:
        return 0.0

    return supported_claims / total_claims


# ---------------------------------------------------------
# Citation accuracy scoring
# ---------------------------------------------------------

def check_citations(citations, expected_sources):
    """Check whether retrieved citation sources match expected sources."""

    if not citations:
        return 0.0

    retrieved_sources = {
        details["source"]
        for details in citations.values()
    }

    matching_sources = retrieved_sources.intersection(expected_sources)

    if not expected_sources:
        return 0.0

    return len(matching_sources) / len(expected_sources)


# ---------------------------------------------------------
# Evaluate one question
# ---------------------------------------------------------

def score_answer(example):
    """Evaluate one RAG question."""

    result = answer_with_citations(
        example["question"],
        k=2
    )

    correctness = judge_expected_points(
        answer=result["answer"],
        expected_points=example["expected_points"]
    )

    grounding = judge_grounding(
        answer=result["answer"],
        citations=result["citations"]
    )

    citation_accuracy = check_citations(
        citations=result["citations"],
        expected_sources=example["expected_sources"]
    )

    return {
        "question": example["question"],
        "answer": result["answer"],
        "correctness": correctness,
        "grounding": grounding,
        "citation_accuracy": citation_accuracy,
        "citations": result["citations"]
    }


# ---------------------------------------------------------
# Evaluate complete test set
# ---------------------------------------------------------

def evaluate_rag():
    """Evaluate the complete RAG system."""

    rows = [
        score_answer(example)
        for example in test_set
    ]

    total = len(rows)

    if total == 0:
        return {
            "questions": 0,
            "avg_correctness": 0.0,
            "avg_grounding": 0.0,
            "avg_citation_accuracy": 0.0,
            "failures": []
        }

    summary = {
        "questions": total,
        "avg_correctness": sum(
            row["correctness"] for row in rows
        ) / total,

        "avg_grounding": sum(
            row["grounding"] for row in rows
        ) / total,

        "avg_citation_accuracy": sum(
            row["citation_accuracy"] for row in rows
        ) / total,

        "failures": [
            row
            for row in rows
            if min(
                row["correctness"],
                row["grounding"],
                row["citation_accuracy"]
            ) < 1
        ]
    }

    return summary, rows


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

def print_results(summary, rows):
    """Print evaluation results."""

    print("=" * 60)
    print("FInee.ai - RAG EVALUATION")
    print("=" * 60)

    print("\nQUESTION RESULTS")
    print("-" * 60)

    for index, row in enumerate(rows, start=1):
        print(f"\nQuestion {index}")
        print(f"Question           : {row['question']}")
        print(f"Correctness        : {row['correctness']:.2f}")
        print(f"Grounding          : {row['grounding']:.2f}")
        print(f"Citation Accuracy  : {row['citation_accuracy']:.2f}")

        print("Sources:")
        for details in row["citations"].values():
            print(
                f"  - {details['source']} "
                f"(chunk {details['chunk_index']})"
            )

    print("\n" + "=" * 60)
    print("OVERALL QUALITY")
    print("=" * 60)

    print(f"Questions           : {summary['questions']}")
    print(
        f"Average Correctness: "
        f"{summary['avg_correctness']:.2f}"
    )
    print(
        f"Average Grounding  : "
        f"{summary['avg_grounding']:.2f}"
    )
    print(
        f"Average Citation   : "
        f"{summary['avg_citation_accuracy']:.2f}"
    )

    print("\n" + "=" * 60)
    print("FAILURE SUMMARY")
    print("=" * 60)

    if not summary["failures"]:
        print("No failures detected.")
    else:
        for failure in summary["failures"]:
            print(f"\nQuestion: {failure['question']}")
            print(
                f"Correctness       : "
                f"{failure['correctness']:.2f}"
            )
            print(
                f"Grounding         : "
                f"{failure['grounding']:.2f}"
            )
            print(
                f"Citation Accuracy : "
                f"{failure['citation_accuracy']:.2f}"
            )

    print("\n" + "=" * 60)
    print("RAG EVALUATION COMPLETED")
    print("=" * 60)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    summary, rows = evaluate_rag()
    print_results(summary, rows)


if __name__ == "__main__":
    main()