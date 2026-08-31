# Utility and Maintenance Scripts

This directory houses administrative, maintenance, demonstration, and ingestion scripts for local development, data loading, database migrations, and evaluation benchmarks.

## Available Scripts

- `prompt_template_demo.py`: Demonstrates reusable prompt design, runtime variable injection, error handling, and multi-feature template reuse.
- `demonstrate_temperature.py`: Compares output consistency across LLM temperature settings (0.0 vs 1.0).
- `token_count_demo.py`: Token counting and cost estimation across sample financial documents.
- `token_cost_estimator.py`: CLI token and cost estimator for input prompt and answer files.

## Planned Scripts
- `ingest_documents.py`: Batch ingestion pipeline runner for financial filings, factsheets, and disclosures.
- `init_db.py`: Database schema setup and pgvector extension initialization.
- `evaluate_retrieval.py`: Retrieval evaluation runner comparing Top-K results against benchmark question-answer sets.
