"""Demonstration script for Embeddings Fundamentals & Vector Representation using LangChain.

Demonstrates:
1. Generating embeddings for short sample texts using LangChain interfaces (embed_documents & embed_query).
2. Reporting and verifying vector dimensions and uniform length (1536 dimensions).
3. Comparing similar vs. dissimilar text pairs using cosine similarity.
4. Explaining what embedding vectors represent in semantic search.
5. Saving results and sample vector outputs to JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# pyrefly: ignore [missing-import]
from src.embeddings.embedder import (
    DEFAULT_VECTOR_DIMENSION,
    FIneeLangChainEmbeddings,
    cosine_similarity,
    embed,
    embed_texts,
    get_langchain_embeddings,
    verify_dimensions,
)

OUTPUT_FILE = PROJECT_ROOT / "outputs" / "evaluations" / "embedding_similarity_demo.json"


EXPLANATION_NOTE = (
    "What Embedding Vectors Represent in Plain Terms:\n\n"
    "1. Vectors as Coordinates of Meaning:\n"
    "   An embedding vector is not a random identifier, integer hash, or simple keyword counter. "
    "It is an array of floating-point numbers that positions text within a continuous, high-dimensional "
    "semantic coordinate space (e.g. 1536 dimensions).\n\n"
    "2. Semantic Proximity in Vector Space:\n"
    "   During model training, the embedding model learns to map conceptual relationships. Texts expressing "
    "the same intent or semantic concept (such as 'How do I reset my account password?' and 'Steps to recover "
    "access to my login') are mapped to vectors pointing in nearly identical geometric directions. "
    "Conversely, unrelated topics ('The cafeteria menu has pasta today') point in divergent directions.\n\n"
    "3. Directional Comparison via Cosine Similarity:\n"
    "   By computing the cosine of the angle between two vectors, we quantify their semantic similarity on a "
    "scale from -1.0 to +1.0. A score near 1.0 indicates strong semantic equivalence, regardless of whether "
    "the texts share any exact keywords.\n\n"
    "4. Foundation of RAG Semantic Retrieval:\n"
    "   In a Retrieval-Augmented Generation (RAG) pipeline, knowledge chunks are embedded and indexed in a "
    "vector database. When a user submits a question, it is converted into an embedding vector, enabling fast "
    "nearest-neighbor search to retrieve conceptually relevant chunks even when phrasing differs entirely.\n\n"
    "5. Standardized with LangChain:\n"
    "   Using LangChain's Embeddings interface (embed_documents & embed_query) provides unified compatibility "
    "across vector stores, indexing pipelines, and production retrieval chains."
)


def run_embedding_demonstration() -> Dict[str, Any]:
    """Runs the embedding fundamentals demonstration and returns output payload."""
    print("=" * 80)
    print("FInee.ai - Embeddings Fundamentals & Vector Representation (with LangChain)")
    print("=" * 80)

    # Initialize LangChain Embeddings provider
    langchain_embedder = get_langchain_embeddings()
    print(f"Loaded LangChain Embeddings Provider: {type(langchain_embedder).__name__}")

    # --- Task 1: Sample Texts ---
    sample_texts = [
        "How do I reset my account password?",          # Text 0 (Account Access A)
        "Steps to recover access to my login",           # Text 1 (Account Access B - Similar to 0)
        "The cafeteria menu has pasta today",            # Text 2 (Unrelated - Food/Cafeteria)
        "What is the annual yield on a high-interest savings account?", # Text 3 (Finance A)
        "How much interest does a high-yield savings deposit earn annually?", # Text 4 (Finance B - Similar to 3)
        "The football match was postponed due to heavy rain", # Text 5 (Unrelated - Sports/Weather)
    ]

    print("\n[Task 1] Generating Embeddings via LangChain (embed_documents):")
    for idx, text in enumerate(sample_texts):
        print(f"  [{idx}] \"{text}\"")

    # Using standard LangChain embed_documents method
    embeddings: List[List[float]] = langchain_embedder.embed_documents(sample_texts)

    # --- Task 2: Vector Dimension Reporting and Validation ---
    print("\n[Task 2] Vector Dimension & Representation:")
    dim_report = verify_dimensions(embeddings)
    dimension = dim_report["dimension"]
    print(f"  • Vector Dimension: {dimension}")
    print(f"  • Total Embeddings Generated: {dim_report['count']}")
    print(f"  • All Dimensions Uniform: {dim_report['is_uniform']}")
    print(f"  • First 8 values of Text [0]: {embeddings[0][:8]}")
    print(f"  • First 8 values of Text [1]: {embeddings[1][:8]}")
    print(f"  • First 8 values of Text [2]: {embeddings[2][:8]}")

    # Confirm dimension uniformity
    assert dim_report["is_uniform"], "Error: Embedding vectors have inconsistent dimensions!"

    # --- Task 3: Similar vs Dissimilar Comparisons ---
    print("\n[Task 3] Semantic Similarity Comparisons (Cosine Similarity):")

    # Pair 1: Password reset vs. Login recovery (Similar)
    sim_pair_1 = cosine_similarity(embeddings[0], embeddings[1])
    # Pair 2: Password reset vs. Cafeteria pasta (Dissimilar)
    dissim_pair_1 = cosine_similarity(embeddings[0], embeddings[2])

    # Pair 3: High-yield savings yield vs. Interest earned (Similar)
    sim_pair_2 = cosine_similarity(embeddings[3], embeddings[4])
    # Pair 4: High-yield savings vs. Football weather (Dissimilar)
    dissim_pair_2 = cosine_similarity(embeddings[3], embeddings[5])

    print("\n  Scenario A (Authentication / Account Recovery):")
    print(f"    - Similar Pair   (Text [0] vs Text [1]): Cosine = {sim_pair_1:.4f}")
    print(f"    - Dissimilar Pair (Text [0] vs Text [2]): Cosine = {dissim_pair_1:.4f}")
    print(f"    - Similar > Dissimilar? {sim_pair_1 > dissim_pair_1} (Difference: +{sim_pair_1 - dissim_pair_1:.4f})")

    print("\n  Scenario B (Financial Product vs Unrelated Event):")
    print(f"    - Similar Pair   (Text [3] vs Text [4]): Cosine = {sim_pair_2:.4f}")
    print(f"    - Dissimilar Pair (Text [3] vs Text [5]): Cosine = {dissim_pair_2:.4f}")
    print(f"    - Similar > Dissimilar? {sim_pair_2 > dissim_pair_2} (Difference: +{sim_pair_2 - dissim_pair_2:.4f})")

    # --- Task 4: Explanation of Vector Representation ---
    print("\n[Task 4] Conceptual Explanation:")
    print("-" * 80)
    print(EXPLANATION_NOTE)
    print("-" * 80)

    # --- Task 5: Structured Payload & File Output ---
    output_data: Dict[str, Any] = {
        "status": "success",
        "framework": "LangChain",
        "vector_dimension": dimension,
        "sample_count": len(sample_texts),
        "is_dimension_uniform": dim_report["is_uniform"],
        "samples": [
            {
                "id": idx,
                "text": text,
                "dimension": len(embeddings[idx]),
                "first_8_values": [round(v, 6) for v in embeddings[idx][:8]],
            }
            for idx, text in enumerate(sample_texts)
        ],
        "comparisons": [
            {
                "comparison_name": "Account Password Reset vs Login Recovery (Similar)",
                "text_a": sample_texts[0],
                "text_b": sample_texts[1],
                "category": "similar",
                "cosine_similarity": round(sim_pair_1, 4),
            },
            {
                "comparison_name": "Account Password Reset vs Cafeteria Menu (Dissimilar)",
                "text_a": sample_texts[0],
                "text_b": sample_texts[2],
                "category": "dissimilar",
                "cosine_similarity": round(dissim_pair_1, 4),
            },
            {
                "comparison_name": "High-Yield Savings Yield vs Interest Earned (Similar)",
                "text_a": sample_texts[3],
                "text_b": sample_texts[4],
                "category": "similar",
                "cosine_similarity": round(sim_pair_2, 4),
            },
            {
                "comparison_name": "High-Yield Savings vs Football Match Weather (Dissimilar)",
                "text_a": sample_texts[3],
                "text_b": sample_texts[5],
                "category": "dissimilar",
                "cosine_similarity": round(dissim_pair_2, 4),
            },
        ],
        "ranking_validation": {
            "scenario_a_similar_higher": bool(sim_pair_1 > dissim_pair_1),
            "scenario_b_similar_higher": bool(sim_pair_2 > dissim_pair_2),
        },
        "explanation": EXPLANATION_NOTE,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n[Task 5] Results saved to: {OUTPUT_FILE}")
    print("=" * 80)
    return output_data


if __name__ == "__main__":
    run_embedding_demonstration()
