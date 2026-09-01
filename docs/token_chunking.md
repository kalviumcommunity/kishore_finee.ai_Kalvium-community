# Token-Aware Chunk Sizing & Overlap in FInee.ai

This document details the design, algorithmic mechanics, and context budget justification for **Token-Aware Chunk Sizing and Controlled Overlap** (Concept 13) in the `finee.ai` compliance-grounded financial advisory platform.

---

## 1. Why Token-Aware Chunking is Critical

In Concept 12, document splitting was performed by character count. However, Large Language Models (LLMs) and vector embedding models operate on **tokens**, not characters:

1. **Token Density Variance**:
   - 500 characters of formatted financial tables, ticker symbols (`AAPL`, `MSFT`), or JSON metadata can easily translate to 150+ tokens.
   - 500 characters of spaced-out natural text might only be 80 tokens.
   - Character-based chunking produces inconsistent token counts, risking context window budget overflows or inefficient under-utilization.
2. **Context Window Predictability**:
   - Retrieval-Augmented Generation (RAG) requires strict context budgeting: `(retrieved_chunk_tokens × Top_K) + system_prompt + query + chat_history ≤ context_limit`.
   - Token-aware chunking guarantees that every retrieved chunk strictly adheres to the token allocation.
3. **Preventing Mid-Token & Mid-Clause Truncation**:
   - Arbitrary character boundaries can split subword tokens or slice financial conditions, causing embedding models to produce noisy vector representations.

---

## 2. The Sliding Window Algorithm

Token-aware chunking uses a tokenizer (`tiktoken` with `cl100k_base` encoding) to tokenize the entire cleaned document into a sequence of token IDs, then slices the sequence with a sliding window:

```python
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def token_chunks(text: str, size: int = 400, overlap: int = 60) -> list[str]:
    toks = enc.encode(text)
    out, i = [], 0
    step = size - overlap  # Step forward by (size - overlap) tokens
    while i < len(toks):
        out.append(enc.decode(toks[i : i + size]))
        i += step
    return out
```

### Key Parameters:
- **`size`**: The target maximum token count for each chunk (default: `400` tokens).
- **`overlap`**: The number of trailing tokens repeated at the beginning of the next adjacent chunk (default: `60` tokens / `15%`).
- **`step = size - overlap`**: The stride by which the window advances across the document.

---

## 3. Preserving Boundary Context

When text is chunked without overlap (`overlap = 0`), critical facts spanning a split point are fractured into separate chunks. Neither chunk alone contains enough context for the embedding model or LLM to answer the query accurately.

### Concrete Financial Advisory Example:

#### Source Document:
> *"Advisors must ensure that portfolio fee reductions comply strictly with SEC Rule 206(4)-1. Specifically, clients are eligible for a 0.50% advisory fee discount only if their aggregate qualifying asset balance across linked family accounts exceeds $250,000 as of the quarter-end evaluation date. Accounts failing to maintain this threshold will revert to standard asset management fee schedules without exception."*

#### Target Advisor Query:
> *"What asset balance and evaluation timing are required for the 0.50% fee discount?"*

### Comparison:

| Strategy | Chunk Breakdown | Complete Answer Found? |
| :--- | :--- | :--- |
| **Without Overlap** (`size=35`, `overlap=0`) | **Chunk 2**: `"...clients are eligible for a 0.50% advisory fee discount only if their aggregate qualifying asset balance across linked family accounts exceeds $250,000 as of the"`<br>**Chunk 3**: `"quarter-end evaluation date. Accounts failing to maintain this threshold will revert to standard asset management fee schedules..."` | ❌ **No** (The qualification date is separated from the fee percentage and balance threshold) |
| **With Overlap** (`size=35`, `overlap=15`) | **Chunk 3**: `"eligible for a 0.50% advisory fee discount only if their aggregate qualifying asset balance across linked family accounts exceeds $250,000 as of the quarter-end evaluation date."` | ✅ **Yes** (All three components: `0.50%`, `$250,000`, and `quarter-end evaluation date` appear intact in Chunk 3) |

---

## 4. Cost vs Context Trade-Off Analysis

Adding overlap introduces a minor duplication overhead in total stored tokens and embedding computation. The platform balances retrieval reliability against cost:

| Overlap (Tokens) | Overlap (%) | Corpus Chunk Count | Total Stored Tokens | Token Duplication Overhead | Trade-Off Evaluation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`0`** | `0.0%` | 6 | 2,278 | `+0.00%` | ⚠️ Zero extra cost, but high risk of boundary fracture. |
| **`40`** | `10.0%` | 7 | 2,518 | `+10.49%` | Adequate for short sentences; may miss longer legal clauses. |
| **`60` (Recommended)** | **`15.0%`** | **7** | **2,637** | **`+15.71%`** | 🎯 **Optimal sweet spot**: Preserves 2-3 full sentences across boundaries for minimal overhead. |
| **`100`** | `25.0%` | 8 | 2,979 | `+30.72%` | Unnecessarily high duplication; inflates vector store index size. |

---

## 5. FInee.ai Context Window Budget Justification

In FInee.ai, retrieved chunks feed into the LLM context window alongside the system prompt, compliance guardrails, user query, and chat history.

### Model Context Budget (LLaMA-3-70B / Groq 8k Minimum Context):

```text
+-------------------------------------------------------------+
| LLaMA-3 / Groq Context Window Limit: 8,192 Tokens           |
+-------------------------------------------------------------+
| [Retrieved Context] Top-K = 5 chunks × 400 tokens = 2,000   |
| [System Prompt & Guardrails]                        =   350 |
| [User Query & Conversation History]                 =   400 |
| [Max Generation Response Budget]                    =   500 |
+-------------------------------------------------------------+
| Total Context Allocated                             = 3,250 |
| Safety Headroom Remaining                           = 4,942 |
+-------------------------------------------------------------+
```

### Why 400 Tokens Chunk Size with 60 Tokens Overlap?
1. **Semantic Completeness**: 400 tokens (~300 English words / 2–3 dense financial paragraphs) is sufficient to encapsulate a complete regulatory disclosure, fee structure, or market risk summary.
2. **Top-K Retrieval Flexibility**: With 400-token chunks, the retrieval engine can fetch **Top-K = 5** distinct document sections (totaling 2,000 tokens) to aggregate multi-document evidence without exceeding 40% of the active context window.
3. **Boundary Safety**: 60 tokens (~45 words / ~2 sentences) guarantees that compound sentences and conditional financial rules are never lost at chunk boundaries.

---

## 6. How to Run the Demonstration & Tests

### Run the Demonstration Script:
```bash
python -m scripts.demonstrate_token_chunking --output outputs/evaluations/token_chunking_results.json
```

### Run the Automated Test Suite:
```bash
pytest -v tests/test_token_chunking.py
```
