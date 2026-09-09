# Retrieval Guardrails & Safe Refusal in FInee.ai

This document outlines the architecture, relevance thresholds, pre-generation guardrails, and safe refusal behavior implemented in the `finee.ai` compliance-grounded financial advisory RAG system.

---

## 1. Why RAG Should Not Answer Every Question

In general chatbots, models often attempt to provide plausible-sounding answers even when user queries are out-of-domain, vague, or unsupported by verified knowledge. 

In a **regulated financial advisory** environment, answering questions without sufficient verified evidence creates severe regulatory and legal liabilities:
- **Misleading Advice**: Stating incorrect fee schedules, redemption penalties, or tax rules can lead to financial losses and regulatory penalties.
- **Unverified Recommendations**: Speculating on investments outside the authorized product catalog breaches advisory compliance.
- **Boundary Preservation**: System queries regarding unindexed topics (e.g. employee cafeteria menus, third-party crypto tokens, unauthorized policy changes) must be strictly declined.

A production-grade RAG pipeline must be capable of **saying "I don't know" gracefully and deterministically**.

---

## 2. What Hallucination Means in FInee.ai

In `finee.ai`, **hallucination** is defined as any generated response that:
1. Invents numerical figures (e.g., fee rates, yields, balances, penalty percentages).
2. Fabricates dates or timelines (e.g., invoice dates, maturity dates, grace periods).
3. Asserts client identities or transaction records not present in the retrieved chunks.
4. Extrapolates beyond verified compliance documents.
5. Attributes claims to non-existent or irrelevant sources.

By halting execution prior to calling the LLM whenever evidence is weak, the retrieval guardrail eliminates the primary driver of hallucination: **forcing an LLM to answer from noisy or irrelevant context**.

---

## 3. How the Relevance Threshold Works

Every chunk in `finee.ai` has an associated numerical similarity or re-ranking relevance score ($0.0 \le \text{score} \le 1.0$ for cosine similarity):

$$\text{Strong Chunk} \iff \text{score} \ge \text{MIN\_TOP\_SCORE}$$

The system evaluates two criteria via `retrieval_is_strong(chunks)`:
1. **Top Score Criterion**: $\max(\text{scores}) \ge \text{MIN\_TOP\_SCORE}$ (default: `0.72`).
2. **Supporting Chunks Criterion**: $\sum \mathbf{1}_{(\text{score} \ge \text{MIN\_TOP\_SCORE})} \ge \text{MIN\_SUPPORTING\_CHUNKS}$ (default: `1`).

```python
MIN_TOP_SCORE = 0.72           # Minimum similarity required for top chunk
MIN_SUPPORTING_CHUNKS = 1      # Minimum number of strong chunks required
RETRIEVAL_TOP_K = 4            # Candidate set evaluated
```

---

## 4. Difference Between Empty, Weak, and Strong Retrieval

| Retrieval Category | Diagnostic Status | Score Profile | Pipeline Action | LLM Invoked? | Sources Returned |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **Empty Retrieval** | `refused_empty_context` | 0 chunks retrieved ($\text{top\_score} = 0.0$) | Safe Refusal | ❌ No | `[]` |
| **Weak Retrieval** | `refused_weak_context` | Chunks retrieved but $\text{top\_score} < 0.72$ (e.g., $0.54$) | Safe Refusal | ❌ No | `[]` |
| **Insufficient Support** | `refused_insufficient_support` | $\text{top\_score} \ge 0.72$ but $< \text{MIN\_SUPPORTING\_CHUNKS}$ strong chunks | Safe Refusal | ❌ No | `[]` |
| **Strong Retrieval** | `answered` | $\text{top\_score} \ge 0.72$ and $\ge \text{MIN\_SUPPORTING\_CHUNKS}$ strong chunks | Context Injection $\to$ LLM Generation | ✅ Yes | `[ [1] doc.pdf#1, ... ]` |

---

## 5. Why the Guardrail Runs Before LLM Generation

Running quality validation **before** calling the language model delivers three decisive architectural advantages:

```
User Question
     ↓
Vector Retrieval (Top-K)
     ↓
Re-ranking (if enabled)
     ↓
[ Retrieval Strength Guardrail ]  ──(Weak / Empty)──→  Safe Refusal (0 LLM Cost, 0 Hallucination)
     ↓ (Strong)
Context Injection & Token Budgeting
     ↓
Grounded LLM Generation Call
     ↓
Answered with Verified Citations
```

1. **Zero Hallucination Guarantee**: When no valid evidence exists, the LLM is never invoked, completely eliminating the opportunity for model drift or fabricated answers.
2. **Cost & Latency Reduction**: Refused queries return in $< 1 \text{ ms}$ without consuming commercial LLM tokens or API latency.
3. **No Phantom Citations**: Refusal responses return `sources: []`, preventing confusing or deceptive citations to irrelevant documents.

---

## 6. How Threshold Values Should Be Tuned

Threshold values should not be set arbitrarily; they are calibrated using gold-standard evaluation datasets:

1. **Benchmark Datasets**: Build evaluation pairs containing:
   - **In-domain queries**: Expecting verified answers ($\text{expected\_status} = \text{"answered"}$).
   - **Out-of-domain queries**: Expecting refusals ($\text{expected\_status} = \text{"refused\_weak\_context"}$).
   - **Adversarial / distractor queries**: Unrelated terms sharing common words.
2. **Precision vs. Recall Curve**:
   - Setting `MIN_TOP_SCORE` too high (e.g. `0.88`) causes **False Refusals** (valid queries rejected).
   - Setting `MIN_TOP_SCORE` too low (e.g. `0.45`) causes **False Acceptances** (weak context reaching LLM).
3. **Recommended Baseline**: `0.72` with cosine similarity provides a balanced operational threshold for financial document retrieval.

---

## 7. The False Refusal Risk (Refusing Too Often)

While safety is critical, overly aggressive guardrails damage user experience:
- If legitimate questions about client fee structures or KYC requirements are refused, users lose trust in the advisory tool.
- Setting `MIN_SUPPORTING_CHUNKS` higher than the number of chunks containing distinct facts can cause valid single-chunk answers to fail.

Therefore, `MIN_TOP_SCORE` (`0.72`) and `MIN_SUPPORTING_CHUNKS` (`1`) are configurable in `Settings` and environment variables so operations teams can calibrate per environment.

---

## 8. Financial and Compliance Protection

In production:
- **Refusal Text**: Standardized compliance-safe response:
  > *"I don't have enough reliable evidence in the approved knowledge base to answer that question."*
- **Audit Logs**: Every query decision logs status (`answered`, `refused_weak_context`, etc.), `top_score`, and `supporting_chunks_count` without storing confidential customer PII or document text.
