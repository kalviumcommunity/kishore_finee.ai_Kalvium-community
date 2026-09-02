# Utility and Maintenance Scripts

This directory houses administrative, maintenance, demonstration, and ingestion scripts for local development, data loading, database migrations, and evaluation benchmarks.

## Available Scripts

### Embeddings & Semantic Search
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

## Planned Scripts
- `ingest_documents.py`: Batch ingestion pipeline runner for financial filings, factsheets, and disclosures.
- `init_db.py`: Database schema setup and pgvector extension initialization.
- `evaluate_retrieval.py`: Retrieval evaluation runner comparing Top-K results against benchmark question-answer sets.
