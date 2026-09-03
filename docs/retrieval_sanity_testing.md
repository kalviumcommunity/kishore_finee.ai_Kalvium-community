# Embedding Retrieval Sanity Testing

This document details the deterministic retrieval sanity testing layer implemented for `finee.ai` before integrating full-scale vector databases or production retrieval pipelines.

---

## 1. Why Embedding Sanity Tests Are Needed

Generating dense embeddings is only the first half of a semantic pipeline. Before persisting vectors into a vector database or trusting them in production RAG retrieval, we must verify that:
- **Semantic Proximity Holds**: Queries retrieve domain-relevant chunks rather than random or distractor chunks.
- **Model Consistency is Maintained**: Query vectors and chunk vectors inhabit the identical coordinate space.
- **Vectors Are Valid & Normalized**: There are no zero-norm, NaN, or non-numeric vectors corrupting similarity calculations.
- **Provenance Remains Intact**: Ranked outputs preserve original chunk text and metadata without mutations.

---

## 2. What Is a Known Test Case?

A **known test case** is a curated query paired with its ground-truth source document or chunk:

```json
{
    "query": "What is the advisory fee structure and billing schedule?",
    "expected_source": "fee-schedule.pdf",
    "expected_chunk_id": 0
}
```

By testing queries against known corpus sources, we can objectively evaluate whether the top retrieved candidate matches expectations without needing human-in-the-loop inspection.

---

## 3. The "Same Model" Consistency Rule

> [!IMPORTANT]
> Both query strings and corpus chunks must be generated with the identical model (e.g. `text-embedding-3-small`).

If a chunk was embedded using Model A (e.g., `text-embedding-ada-002`) and the query is embedded using Model B (e.g., `text-embedding-3-small`), computing cosine similarity between them yields meaningless noise. The sanity layer detects model mismatches and raises `ModelMismatchError` rather than silently returning corrupted rankings.

---

## 4. Cosine Similarity & Ranking Mechanics

### Mathematical Formulation
$$\text{Cosine Similarity}(A, B) = \frac{A \cdot B}{\|A\| \times \|B\|} = \frac{\sum_{i=1}^n A_i B_i}{\sqrt{\sum_{i=1}^n A_i^2} \times \sqrt{\sum_{i=1}^n B_i^2}}$$

### Ranking Algorithm:
1. **Query Vector Resolution**: Embed the query using the configured `EmbeddingService`.
2. **Validation**: Check for non-zero norms, finite values, matching dimensions, and model compatibility.
3. **Similarity Computation**: Calculate cosine similarity against every chunk embedding.
4. **Preservation & Sorting**: Attach similarity `score` to a copy of each chunk record and sort descending.

```
Query: "What is the advisory fee?"
  ↓
Query Vector [0.93, 0.04, 0.03, ...]
  ↓
Compare against Chunk Vectors
  ├── fee-schedule.pdf (Chunk 0)       --> Score: 0.9921  [Rank 1]
  ├── compliance-policy.pdf (Chunk 0)  --> Score: 0.2140  [Rank 2]
  └── account-security.pdf (Chunk 0)   --> Score: 0.1105  [Rank 3]
```

---

## 5. Interpreting Results & Failure Diagnostics

When a sanity test executes:
- **`[PASS]`**: The highest-ranked chunk originates from the `expected_source`.
- **`[FAIL]`**: The highest-ranked chunk originates from a different source, or an error occurred.

### Diagnostic Checklist on Failure:
When a test fails, the runner inspects possible root causes:
1. **Expected Source Missing**: The `expected_source` file does not exist in the ingested corpus.
2. **Low Overall Score ($< 0.20$)**: The query is too generic, out-of-domain, or semantic overlap is weak.
3. **Competing Source Semantic Overlap**: Another document legitimately addresses the query with higher keyword/semantic overlap.
4. **Text Cleaning Over-Reduction**: Important terms (e.g., numbers, fee percentages) may have been stripped during text cleaning.
5. **Model or Dimension Mismatch**: Embedding parameters were misconfigured.

---

## 6. Example Sanity Report

```text
Embedding Sanity Report
=======================

Tests: 5
Passed: 5
Failed: 0

[PASS]
Query: What is the advisory fee structure and billing schedule?
Expected source: fee-schedule.pdf
Top source: fee-schedule.pdf
Top score: 0.9984

[PASS]
Query: When does the bond fund mature and what is its annual yield?
Expected source: fund-factsheet.pdf
Top source: fund-factsheet.pdf
Top score: 0.9976

[PASS]
Query: How is customer identity verified under KYC and AML rules?
Expected source: compliance-policy.pdf
Top source: compliance-policy.pdf
Top score: 0.9982

[PASS]
Query: What are the account security requirements for password resets?
Expected source: account-security.pdf
Top source: account-security.pdf
Top score: 0.9988

[PASS]
Query: What is the penalty for early withdrawal from fixed term deposits?
Expected source: deposit-agreement.pdf
Top source: deposit-agreement.pdf
Top score: 0.9985

Summary:
- Total tests: 5
- Passed: 5
- Failed: 0
- Pass rate: 100.0%
```

---

## 7. How to Run Sanity Tests

To execute the retrieval sanity checker CLI:
```bash
python -m src.retrieval.sanity_checker
```

To run the automated unit tests:
```bash
pytest tests/test_retrieval_sanity.py -v
```
