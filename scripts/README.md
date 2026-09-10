# Utility and Maintenance Scripts

This directory houses administrative, maintenance, demonstration, and ingestion scripts for local development, data loading, database migrations, and evaluation benchmarks.

## Available Scripts

- `demonstrate_streaming_rag.py`: Demonstrates progressive SSE answer streaming, citation delivery (`[1]`), token timing, error event handling, and exports results to `outputs/evaluations/streaming_rag_demo.json`.
  ```bash
  python scripts/demonstrate_streaming_rag.py
  ```
- `demonstrate_filtered_hybrid_search.py`: Demonstrates metadata filtering, unfiltered vs filtered precision comparison, exact keyword lexical scoring, and weighted hybrid ranking. Exports to `outputs/evaluations/metadata_filtering_hybrid_search_results.json` and `outputs/evaluations/filtered_hybrid_search_demo.json`.

  ```bash
  python scripts/demonstrate_filtered_hybrid_search.py
  ```
- `demonstrate_retrieval.py`: Demonstrates Top-K similarity search, same-model query embedding, score and metadata inspection, changing-k context comparison (k=1, 3, 5), and export to `outputs/evaluations/similarity_search_retrieval_results.json` and `outputs/evaluations/top_k_retrieval_demo.json`.
  ```bash
  python scripts/demonstrate_retrieval.py
  ```

### Embeddings & Semantic Search
- `demonstrate_batch_embeddings.py`: Demonstrates chunk batching, rate-limit retry with exponential backoff, cost estimation, and skip-on-rerun idempotency. Outputs to `outputs/evaluations/batch_embedding_summary.json`.
  ```bash
  python scripts/demonstrate_batch_embeddings.py
  ```
- `demonstrate_embeddings.py`: Generates text embeddings, validates vector dimensions (1536), computes cosine similarities for similar and dissimilar text pairs, and exports evaluation JSON reports to `outputs/evaluations/embedding_similarity_demo.json`.
  ```bash
  python scripts/demonstrate_embeddings.py
  ```

### Ingestion & Chunking
- `demonstrate_token_chunking.py`: Demonstrates token-aware document chunking and boundary overlap strategies using tiktoken.
  ```bash
  python scripts/demonstrate_token_chunking.py
  ```
- `token_count_demo.py`: Analyzes token counts across documents and models.
  ```bash
  python scripts/token_count_demo.py
  ```
- `token_cost_estimator.py`: Calculates cost projections for token processing across models.

### LLM & Model Parameters
- `demonstrate_temperature.py`: Demonstrates temperature variance and deterministic output controls for compliance.
- `prompt_template_demo.py`: Demonstrates reusable prompt design, runtime variable injection, error handling, and multi-feature template reuse.
- `demonstrate_temperature.py`: Compares output consistency across LLM temperature settings (0.0 vs 1.0).
- `token_count_demo.py`: Token counting and cost estimation across sample financial documents.
- `token_cost_estimator.py`: CLI token and cost estimator for input prompt and answer files.

## Planned Scripts
- `ingest_documents.py`: Batch ingestion pipeline runner for financial filings, factsheets, and disclosures.
- `init_db.py`: Database schema setup and pgvector extension initialization.
- `evaluate_retrieval.py`: Retrieval evaluation runner comparing Top-K results against benchmark question-answer sets.
