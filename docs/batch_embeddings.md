# Batch Embedding & Rate/Cost Management

## Overview

Embedding small corpora (e.g., 5–10 chunks) is straightforward, but embedding thousands of chunks in production requires a pipeline that is **efficient**, **resilient**, **resumable**, and **polite to provider APIs**. 

FInee.ai provides a specialized `BatchEmbedder` module that batches embedding requests, automatically recovers from rate-limiting errors using exponential backoff, tracks token usage and financial cost, and skips previously embedded chunks across re-runs.

---

## Key Architecture Concepts

### 1. Batching Chunks
Sending one HTTP request per chunk causes significant network roundtrip latency and high request overhead. Batching groups multiple chunks into single API requests.

```python
def batches(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]
```

- **Configurable Batch Size**: Sized to fit provider constraints (e.g., 32, 64, or 128 chunks per request).
- **Reduced Network Overhead**: Slashes connection establishment and HTTP handshake costs.

---

### 2. Exponential Backoff Retry Strategy
Rate limits (HTTP 429) and transient server errors (HTTP 500, 502, 503, 504) are expected at scale. The pipeline applies exponential backoff before retrying:

$$\text{wait\_seconds} = \text{initial\_wait} \times (\text{backoff\_base}^{\text{attempt}})$$

```python
def embed_with_retry(texts, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return client.embeddings.create(model=MODEL, input=texts)
        except Exception as error:
            if attempt == max_attempts - 1:
                raise
            wait_seconds = 2 ** attempt
            time.sleep(wait_seconds)
```

- **Politeness**: Prevents thundering herd problems against OpenAI/provider endpoints.
- **Observability**: Records all retry events and permanent failures in the final run summary.

---

### 3. Token & Cost Estimation
Tracking token consumption provides full transparency and budget control before and after large indexing operations.

$$\text{Estimated Cost (USD)} = \frac{\text{Total Input Tokens}}{1,000} \times \text{Price per 1K Tokens}$$

```python
PRICE_PER_1K_TOKENS = 0.00002  # text-embedding-3-small ($0.02 / 1M tokens)

estimated_cost = (summary["input_tokens"] / 1000) * PRICE_PER_1K_TOKENS
```

---

### 4. Idempotency & Resumable Re-runs
If an embedding job crashes or new documents are incrementally ingested, the pipeline checks the existing embeddings store and filters out already-processed chunks:

```python
pending_chunks = [
    chunk for chunk in all_chunks
    if str(chunk["id"]) not in existing_embedding_ids
]
```

- **Zero Wasted Cost**: Avoids re-embedding chunks that already have valid vectors.
- **Fault Tolerance**: Seamlessly resumes from the last completed batch.

---

## Sample Run Summary Artifact

When executing `scripts/demonstrate_batch_embeddings.py`, the pipeline emits a structured run summary:

```json
{
  "total_chunks": 12,
  "skipped_existing": 0,
  "embedded": 12,
  "failed": 0,
  "input_tokens": 204,
  "estimated_cost_usd": 0.000004,
  "batches_processed": 3,
  "retry_count": 1,
  "failed_chunk_ids": [],
  "errors": []
}
```

On an immediate re-run over the same corpus:

```json
{
  "total_chunks": 12,
  "skipped_existing": 12,
  "embedded": 0,
  "failed": 0,
  "input_tokens": 0,
  "estimated_cost_usd": 0.0,
  "batches_processed": 0,
  "retry_count": 0,
  "failed_chunk_ids": [],
  "errors": []
}
```

---

## Running the Demonstration

To execute the batch embedding demonstration script:

```bash
python scripts/demonstrate_batch_embeddings.py
```

To run the automated test suite:

```bash
pytest tests/test_batch_embeddings.py -v
```
