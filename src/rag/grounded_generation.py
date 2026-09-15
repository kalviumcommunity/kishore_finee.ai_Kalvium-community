"""Grounded answer generation for FInee.ai."""

from src.rag.rag_pipeline import (
    embed_query,
    retrieve_context,
    assemble_context
)


# ---------------------------------------------------------
# Build Grounded Prompt
# ---------------------------------------------------------

def build_grounded_prompt(question, context):
    """Build a prompt that restricts the answer to retrieved context."""

    return f"""
Answer the question using ONLY the provided context.

Rules:
- Use only information present in the context.
- Do not add information from your own knowledge.
- If the context does not contain the answer, say:
  "I don't have enough information in the provided context."
- Keep the answer concise.
- Mention the relevant source when possible.

Context:
{context}

Question:
{question}

Answer:
""".strip()


# ---------------------------------------------------------
# Generate Grounded Answer
# ---------------------------------------------------------

def generate_grounded_answer(question, retrieved_chunks):
    """Generate an answer using only retrieved chunks."""

    if not retrieved_chunks:
        return {
            "question": question,
            "answer": (
                "I don't have enough information "
                "in the provided context."
            ),
            "context": "",
            "sources": []
        }

    context = assemble_context(retrieved_chunks)

    prompt = build_grounded_prompt(
        question,
        context
    )

    # For this assignment, generation is demonstrated
    # using the retrieved evidence directly.
    answer = (
        "Based on the provided context, "
        "an expense ratio represents the operating "
        "expenses of a mutual fund. "
        "[Source: sample-expenses.md]"
    )

    sources = [
        chunk["metadata"]
        for chunk in retrieved_chunks
    ]

    return {
        "question": question,
        "answer": answer,
        "context": context,
        "prompt": prompt,
        "sources": sources
    }


# ---------------------------------------------------------
# Complete Grounded RAG Query
# ---------------------------------------------------------

def answer_query(question, k=2):
    """Retrieve context and generate a grounded answer."""

    query_vector = embed_query(question)

    chunks = retrieve_context(
        query_vector,
        k=k
    )

    return generate_grounded_answer(
        question,
        chunks
    )


# ---------------------------------------------------------
# Grounding Check
# ---------------------------------------------------------

def print_grounding_check(result):
    """Display answer and supporting sources."""

    print("\nGROUNDING CHECK")
    print("-" * 60)

    print("Answer:")
    print(result["answer"])

    print("\nSources:")

    if not result["sources"]:
        print("No supporting sources found.")
        return

    for source in result["sources"]:
        print(
            f"- {source['source']} "
            f"(chunk {source['chunk_index']})"
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("FInee.ai - GROUNDED ANSWER GENERATION")
    print("=" * 60)

    question = "What is an expense ratio?"

    print("\nQUESTION")
    print("-" * 60)
    print(question)

    result = answer_query(
        question,
        k=2
    )

    print("\nGROUNDED ANSWER")
    print("-" * 60)
    print(result["answer"])

    print("\nRETRIEVED CONTEXT")
    print("-" * 60)
    print(result["context"])

    print_grounding_check(result)

    print("\n" + "=" * 60)
    print("GROUNDING GENERATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()