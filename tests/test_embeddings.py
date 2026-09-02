"""Unit test suite for Embeddings Fundamentals & Vector Representation using LangChain."""

from pathlib import Path
import pytest
import numpy as np
from langchain_core.embeddings import Embeddings

from src.embeddings.embedder import (
    DEFAULT_VECTOR_DIMENSION,
    EmbeddingService,
    FIneeLangChainEmbeddings,
    cosine_similarity,
    embed,
    embed_text,
    embed_texts,
    get_langchain_embeddings,
    verify_dimensions,
)
from scripts.demonstrate_embeddings import run_embedding_demonstration, OUTPUT_FILE


class TestLangChainEmbeddings:
    """Test suite for LangChain embedding integration and vector representations."""

    def test_langchain_interface_compliance(self) -> None:
        """Verifies that our embeddings implementation complies with LangChain Embeddings interface."""
        embedder = get_langchain_embeddings()
        assert isinstance(embedder, Embeddings)
        assert hasattr(embedder, "embed_documents")
        assert hasattr(embedder, "embed_query")

    def test_embed_single_text_dimension(self) -> None:
        """Verifies that embedding a single query produces a vector of expected dimension."""
        text = "How do I reset my account password?"
        embedder = get_langchain_embeddings()
        vector = embedder.embed_query(text)

        assert isinstance(vector, list)
        assert len(vector) == DEFAULT_VECTOR_DIMENSION
        assert all(isinstance(v, float) for v in vector)

    def test_embed_batch_texts_uniform_dimensions(self) -> None:
        """Verifies that embed_documents returns vectors with uniform dimensionality."""
        texts = [
            "How do I reset my account password?",
            "Steps to recover access to my login",
            "The cafeteria menu has pasta today",
            "A short phrase",
            "A much longer financial disclaimer and policy explanation for compliance",
        ]
        embedder = get_langchain_embeddings()
        vectors = embedder.embed_documents(texts)

        assert len(vectors) == len(texts)
        verification = verify_dimensions(vectors)
        assert verification["is_uniform"] is True
        assert verification["dimension"] == DEFAULT_VECTOR_DIMENSION
        assert verification["count"] == len(texts)

    def test_embed_convenience_function(self) -> None:
        """Verifies that embed() handles both single strings and lists properly."""
        single_vec = embed("Single input string")
        assert isinstance(single_vec, list)
        assert len(single_vec) == DEFAULT_VECTOR_DIMENSION

        multi_vecs = embed(["First string", "Second string"])
        assert isinstance(multi_vecs, list)
        assert len(multi_vecs) == 2
        assert len(multi_vecs[0]) == DEFAULT_VECTOR_DIMENSION
        assert len(multi_vecs[1]) == DEFAULT_VECTOR_DIMENSION

    def test_cosine_similarity_properties(self) -> None:
        """Verifies mathematical properties of cosine similarity."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        v4 = [-1.0, 0.0, 0.0]

        # Self-similarity should be 1.0
        assert pytest.approx(cosine_similarity(v1, v2), 1e-6) == 1.0

        # Orthogonal vectors should have 0.0 similarity
        assert pytest.approx(cosine_similarity(v1, v3), 1e-6) == 0.0

        # Opposite vectors should have -1.0 similarity
        assert pytest.approx(cosine_similarity(v1, v4), 1e-6) == -1.0

        # Commutativity: sim(a, b) == sim(b, a)
        random_a = [0.5, 0.2, 0.8]
        random_b = [0.1, 0.9, 0.3]
        assert pytest.approx(cosine_similarity(random_a, random_b), 1e-6) == cosine_similarity(random_b, random_a)

    def test_cosine_similarity_validation_errors(self) -> None:
        """Verifies validation on dimension mismatch and empty vectors."""
        with pytest.raises(ValueError, match="Vector dimensions must match"):
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Cannot compute cosine similarity of empty vectors"):
            cosine_similarity([], [])

    def test_similar_vs_dissimilar_ranking(self) -> None:
        """Verifies that conceptually similar texts score higher than dissimilar texts."""
        embedder = get_langchain_embeddings()

        password_query = "How do I reset my account password?"
        login_recovery = "Steps to recover access to my login"
        cafeteria_menu = "The cafeteria menu has pasta today"

        vec_query = embedder.embed_query(password_query)
        vec_recovery = embedder.embed_query(login_recovery)
        vec_menu = embedder.embed_query(cafeteria_menu)

        sim_score = cosine_similarity(vec_query, vec_recovery)
        dissim_score = cosine_similarity(vec_query, vec_menu)

        assert sim_score > dissim_score
        assert (sim_score - dissim_score) > 0.15

    def test_financial_domain_ranking(self) -> None:
        """Verifies ranking on financial domain statements."""
        embedder = get_langchain_embeddings()

        finance_a = "What is the annual yield on a high-interest savings account?"
        finance_b = "How much interest does a high-yield savings deposit earn annually?"
        unrelated = "The football match was postponed due to heavy rain"

        vec_a = embedder.embed_query(finance_a)
        vec_b = embedder.embed_query(finance_b)
        vec_u = embedder.embed_query(unrelated)

        sim_score = cosine_similarity(vec_a, vec_b)
        dissim_score = cosine_similarity(vec_a, vec_u)

        assert sim_score > dissim_score
        assert (sim_score - dissim_score) > 0.20

    def test_demonstration_script_execution(self) -> None:
        """Verifies that the demonstration script runs end-to-end without errors."""
        result = run_embedding_demonstration()

        assert result["status"] == "success"
        assert result["framework"] == "LangChain"
        assert result["vector_dimension"] == DEFAULT_VECTOR_DIMENSION
        assert result["is_dimension_uniform"] is True
        assert len(result["samples"]) == 6
        assert len(result["comparisons"]) == 4
        assert result["ranking_validation"]["scenario_a_similar_higher"] is True
        assert result["ranking_validation"]["scenario_b_similar_higher"] is True
        assert OUTPUT_FILE.exists()
