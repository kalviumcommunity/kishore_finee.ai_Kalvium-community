# Re-ranking Retrieved Candidates

This document details the candidate re-ranking architecture for the `finee.ai` compliance-grounded financial advisory RAG platform.

---

## 1. Overview & Architecture

Vector-based semantic search excels at finding broadly similar documents across millions of records with sub-millisecond latency. However, bi-encoder embedding models compress an entire document chunk into a single fixed vector, occasionally missing subtle sentence-level nuances, specific numerical constraints, or direct evidence relations.

The re-ranking layer introduces a two-stage retrieval pipeline:

```
User Query
   ↓
Stage 1: Initial Vector Retrieval (Bi-Encoder)
   ↓ (Fast, broad candidate recall)
Larger Candidate Set (e.g., K = 10)
   ↓
Stage 2: Cross-Scoring Re-ranking (LLM / Cross-Encoder)
   ↓ (Deep query-chunk pairwise relevance evaluation)
Final Refined Top-K Results (e.g., K = 3)
   ↓
Context for Grounded Financial LLM Response
```

---

## 2. Why Retrieval Uses a Larger Candidate Set ($K=10 \to K=3$)

1. **Recall vs. Precision Balance**:
   - **Stage 1 (Vector Search)** maximizes **recall** by returning the top 10 candidates quickly.
   - **Stage 2 (Re-ranking)** maximizes **precision** by deeply scoring all 10 candidates against the exact query terms to pick the best 3.
2. **Computational Feasibility**:
   - Scoring all 100,000 chunks in a database through an LLM is prohibitively slow and expensive ($O(N)$ LLM calls).
   - Scoring only the top 10 pre-filtered candidates requires only 10 evaluations, keeping latency low and predictable.

---

## 3. Re-ranking Scoring Mechanics

The re-ranking evaluator analyzes the full text of the user query and candidate chunk simultaneously using a focused relevance evaluation prompt:

```
Score how relevant the following chunk is to the query from 0 to 10.

Query:
{query}

Chunk:
{chunk_text}

Return only the numeric score.
```

### Key Scoring Rules:
- **Numerical Output Only**: Output is parsed into a floating-point score clamped between $0.0$ and $10.0$.
- **Data Preservation**: The original chunk text, metadata, stable IDs, and initial vector similarity `score` remain completely untouched.
- **Score Sorting**: Candidates are sorted descending by `rerank_score`, using the initial vector score as a deterministic tie-breaker.

---

## 4. Configuration Parameters

Re-ranking parameters are configured via `src.core.config.settings` and `.env`:

| Setting | Default | Description |
| :--- | :--- | :--- |
| `RERANK_ENABLED` | `true` | Enable or bypass re-ranking |
| `RERANK_CANDIDATE_K` | `10` | Initial candidate set size from vector search |
| `RERANK_FINAL_K` | `3` | Final top results returned after re-ranking |
| `RERANK_MODEL` | `None` *(uses `CHAT_MODEL`)* | Model identifier used for scoring |
| `RERANK_TIMEOUT_SECONDS` | `5.0` | Timeout per re-ranking call |

---

## 5. Before vs. After Ordering Comparison

Consider the query: *"What evidence supports the advisory fee charged to the client?"*

```text
Before re-ranking (Initial Vector Retrieval):
1. vector_score=0.9100 source=general-wealth-guide.md preview="General Financial Advisory Overview: Marcus and wealth..."
2. vector_score=0.8900 source=client-billing-records.pdf preview="Client Advisory Billing Evidence: Advisory fee of $1,250.00..."
3. vector_score=0.8700 source=fee-schedule.pdf preview="Standard Fee Schedule: The annual advisory fee is 0.75%..."

After re-ranking (Relevance-Scored Top-K):
1. vector_score=0.8900 rerank_score=9.50 source=client-billing-records.pdf preview="Client Advisory Billing Evidence: Advisory fee of $1,250.00..."
2. vector_score=0.8700 rerank_score=8.20 source=fee-schedule.pdf preview="Standard Fee Schedule: The annual advisory fee is 0.75%..."
3. vector_score=0.9100 rerank_score=6.10 source=general-wealth-guide.md preview="General Financial Advisory Overview: Marcus and wealth..."
```

**Observation**: `general-wealth-guide.md` scored highest on broad vector similarity due to generic financial terminology, but `client-billing-records.pdf` contained the exact invoice evidence matching the query. Re-ranking successfully promoted the true factual evidence to Rank 1.

---

## 6. Latency & Cost Trade-Offs

```text
Performance & Latency Breakdown:
---------------------------------------------
Initial retrieval candidates: 10
Final results: 3
Initial retrieval latency: 0.0042 seconds
Re-ranking latency: 0.0125 seconds
Total latency: 0.0167 seconds
Re-ranking calls: 10
```

- **Precision Improvement**: Re-ranking eliminates generic high-similarity distractors.
- **Latency Impact**: Sequential or batch LLM scoring introduces latency proportional to `candidate_k`. Keeping `candidate_k = 10` strikes an optimal balance.
- **Cost Impact**: In production with external APIs, $K=10$ adds modest prompt token overhead per user query.

---

## 7. How to Run the Demonstration

To execute the re-ranking demonstration script:
```bash
python scripts/demonstrate_reranking.py
```

To run the re-ranking unit tests:
```bash
pytest tests/test_reranker.py -v
```
