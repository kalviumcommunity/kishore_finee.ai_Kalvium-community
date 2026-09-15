# Context Injection & Prompt Augmentation in FInee.ai

This document provides a comprehensive technical overview of the **Context Injection**, **Token-Budget Control**, and **Prompt Augmentation** subsystems within the `finee.ai` compliance-grounded financial advisory RAG platform.

---

## 1. What Context Injection Does

In a retrieval-augmented generation (RAG) system, **Context Injection** is the critical bridge connecting retrieved vector chunks to the language model's input prompt.

Instead of passing unformatted raw text strings or unconstrained document blobs, context injection:
1. Formats each candidate chunk with standardized citation source markers (e.g. `[1] client-payment-record.pdf#12`).
2. Delimits evidence blocks clearly (`---`) to prevent prompt blending and hallucination.
3. Enforces strict token ceilings to protect the model's completion headroom.
4. Preserves chunk metadata (`source`, `chunk_index`, `document_id`) in parallel structures for downstream citation audits.

---

## 2. Difference Between Retrieval vs. Prompt Augmentation

| Dimension | Vector Retrieval & Re-ranking | Prompt Augmentation & Context Injection |
| :--- | :--- | :--- |
| **Primary Goal** | Maximize semantic recall and rank relevance candidates ($K=10 \to K=3$). | Maximize synthesis precision, enforce token safety, and structure instructions. |
| **Input** | Raw user question and vector database / embeddings index. | User question and ordered candidate chunk objects. |
| **Output** | Ordered list of candidate records with similarity scores. | Structured augmented prompt (`system` + `context` + `question`) within token budget. |
| **Safety Role** | Filters out irrelevant documents. | Instructs model to refuse missing information and cite source markers. |

---

## 3. How Token Budgets Are Calculated

Language models operate within fixed context windows (e.g., 8,192 tokens for standard configurations or 128,000 tokens for long-context models). To guarantee that answer generation never runs out of output tokens or triggers context truncation, token budgets are dynamically partitioned:

$$\text{Model Ceiling} = \text{MAX\_MODEL\_CONTEXT\_TOKENS} - (\text{RESERVED\_ANSWER\_TOKENS} + \text{RESERVED\_INSTRUCTION\_TOKENS})$$

$$\text{Effective Context Budget} = \min(\text{MAX\_CONTEXT\_TOKENS}, \text{Model Ceiling})$$

### Configuration Defaults (`src/core/config.py`):
```python
MAX_MODEL_CONTEXT_TOKENS = 8192      # Total context window
MAX_CONTEXT_TOKENS = 5000            # Upper ceiling for retrieved evidence
RESERVED_ANSWER_TOKENS = 1500        # Output generation reserve
RESERVED_INSTRUCTION_TOKENS = 800    # System prompt and user question reserve
```

### Example Allocation:
- **Total Window**: 8,192 tokens
- **Reserved for LLM Output**: 1,500 tokens
- **Reserved for System Rules & Query**: 800 tokens
- **Maximum Safe Evidence Context**: $\min(5000, 8192 - 2300) = 5,000$ tokens

---

## 4. Why Source Markers Are Required

In regulated financial advisory domains, general text generation without verifiable provenance creates compliance liabilities. Source markers (e.g. `[1] fee-schedule.pdf#0`) serve three vital purposes:

1. **Grounded Attribution**: Allows the model to directly cite which document and chunk index substantiated a numeric fee rate or compliance rule.
2. **Conflict Resolution**: When different policy versions or dates conflict, source markers enable the model to explicitly point out discrepancies between `[1]` and `[2]`.
3. **Auditability**: Downstream verification pipelines can inspect `sources_used` to cross-reference every claim against indexed database records.

### Source Marker Syntax:
- **With chunk index**: `[{index}] {source}#{chunk_index}` (e.g. `[1] client-billing-records.pdf#1`)
- **Without chunk index**: `[{index}] {source}` (e.g. `[3] advisory-agreement.md`)

---

## 5. What Happens When the Context Budget is Exceeded

The `assemble_context` function enforces deterministic budget control:

1. **Ordered Traversal**: Chunks are processed strictly in their retrieved/re-ranked relevance order.
2. **Pre-flight Token Check**: Before adding a chunk, the tokenizer computes the projected token cost of `delimiter + formatted_chunk`.
3. **Budget Stop**: If adding the next chunk would cause total context tokens to exceed `max_context_tokens`, assembly **stops immediately** before exceeding the budget. Chunks lower in the rank are omitted.
4. **Oversized Chunk Protection**: If an individual chunk's standalone token count exceeds the entire budget, it is safely skipped without crashing the pipeline.

---

## 6. How the Final Prompt is Passed to the LLM

The augmented prompt structures instructions into discrete sections:

```text
You are a compliance-grounded financial advisory assistant.
Answer only using the provided context.
Do not use outside knowledge.
If the context does not contain enough information, say:
"I don't have enough information in the provided context."
Do not invent facts, values, dates, identities, policies, or recommendations.
Cite supporting evidence using source markers such as [1] or [2].
If sources conflict, clearly identify the conflict and do not choose a value without sufficient evidence.

Context:
[1] client-billing-records.pdf#1
Client Advisory Billing Evidence: Advisory fee of $1,250.00 for Q3 wealth advisory services was charged to Marcus on 20 August 2026, confirmed via invoice #INV-2026-08.

---

[2] fee-schedule.pdf#0
Standard Fee Schedule: The annual advisory fee is 0.75% of assets under management, calculated and deducted on a quarterly basis in arrears.

Question:
What evidence supports the advisory fee charged to Marcus and what is the fee rate?
```

When invoking OpenAI-compatible chat completion endpoints (`/chat/completions`), the prompt is partitioned into standard message roles:
- `role: "system"` $\to$ Grounded compliance system instruction
- `role: "user"` $\to$ `Context:\n{context}\n\nQuestion:\n{question}`

---

## 7. How Selected Source Metadata is Preserved

To support audit logs and interactive UI citations, `build_prompt` and `assemble_context` return a structured payload preserving complete metadata:

```json
{
  "prompt": "...",
  "context_tokens": 161,
  "selected_chunks": [ ... ],
  "sources_used": [
    {
      "marker": "[1]",
      "source": "client-billing-records.pdf",
      "chunk_index": 1,
      "metadata": {
        "source": "client-billing-records.pdf",
        "document_id": "doc_billing_01",
        "chunk_index": 1,
        "section": "Invoice Verification",
        "approval_status": "approved"
      },
      "id": "doc_billing_01:1"
    }
  ],
  "source_markers": ["[1]", "[2]", "[3]", "[4]"],
  "question": "What evidence supports the advisory fee charged to Marcus?"
}
```

---

## 8. Verification & CLI Usage

### Run Unit Tests:
```bash
pytest tests/test_context_injection.py -v
```

### Run Demonstration:
```bash
python scripts/demonstrate_context_injection.py
```
