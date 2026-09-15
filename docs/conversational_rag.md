# Conversational RAG & Follow-up Query Rewriting in FInee.ai

This document describes the design, architecture, and engineering principles behind conversational history management, query rewriting, and retrieval integration in the `finee.ai` compliance-grounded financial advisory RAG system.

---

## 1. Why Raw Follow-ups Fail in Vector Search

In natural human dialogues, users frequently ask abbreviated follow-up questions that depend on prior conversational context:
- *"What evidence is required for project submission?"* $\to$ *"What about the video?"* $\to$ *"Does it apply to Sprint 2?"*

If raw follow-ups like *"What about the video?"* or *"Does it apply to Sprint 2?"* are embedded directly into a vector space without contextual resolution, vector similarity search fails catastrophically for three reasons:

1. **Loss of Semantic Anchors**: The phrase *"What about the video?"* contains no mention of "project submission", "compliance evidence", "grading rubric", or "sprint requirements".
2. **Nearest-Neighbor Drift in Dense Embeddings**: Embedding models represent queries based on their isolated surface tokens. Dense retrieval for *"What about the video?"* maps to arbitrary generic video documents, media hosting tutorials, or unrelated client video conferencing notices rather than submission rubrics.
3. **Pronoun Ambiguity**: Ambiguous pronouns (*it*, *that*, *they*, *this*) and ellipsis cannot be resolved by vector distance metrics alone. The vector database has no access to conversation session memory.

```
Raw Follow-up: "What about the video?"
     ↓ (Embedded directly)
Vector Search Engine
     ↓
❌ Retrieves: "Video conferencing setup guidelines", "Office security camera policy" (Semantic Drift)
```

By rewriting the conversational follow-up into a standalone retrieval query (*"What video explanation is required for project submission?"*), the query embeds rich semantic anchors that accurately retrieve the target chunks.

---

## 2. Conversation History vs. Retrieval Context

A critical architectural distinction in `finee.ai` is separating **Conversation History** from **Retrieval Context**:

| Characteristic | Conversation History | Retrieval Context |
| :--- | :--- | :--- |
| **Definition** | The chronological sequence of user questions and assistant responses across turns. | The fresh, verified knowledge chunks retrieved from the vector database for a specific query. |
| **Primary Purpose** | Resolving pronouns, conversational ellipsis, and user intent during query rewriting. | Providing the authoritative ground truth for factual answer generation and citation synthesis. |
| **Storage & Lifecycle** | Stored in memory per session; rolled over via FIFO turn/token limits. | Retrieved on-demand per turn; discarded after answer generation. |
| **Trust Model** | Unverified conversational trace; may contain past user assumptions or safe refusals. | Verified, immutable, compliance-cleared enterprise documentation. |
| **Role in Final LLM Prompt** | **Excluded** from generation context (or strictly isolated); only the current turn is answered. | **Injected** directly into the system/context prompt with source markers (`[1] doc#0`). |

Passing raw multi-turn conversation transcripts directly into the final generation prompt risks prompt injection, context bloat, and the model prioritizing conversational dialogue over verified compliance documentation.

---

## 3. How Rewriting Protects Token Budgets

A naive approach to multi-turn RAG is appending all past turns, past retrieved chunks, and past responses into every subsequent prompt. This causes rapid token exhaustion:

$$\text{Naive Prompt Tokens} = \sum_{i=1}^{T} (\text{User}_i + \text{RetrievedChunks}_i + \text{AssistantAnswer}_i)$$

In `finee.ai`, follow-up query rewriting decouples retrieval from conversation size:

1. **Compact Rewriting Call**: A lightweight LLM call receives only the recent conversational dialogue ($< 300\text{ tokens}$) and outputs a concise standalone search query ($< 30\text{ tokens}$).
2. **Fresh Retrieval**: Only the top-$K$ candidate chunks relevant to the *current rewritten query* are fetched and assembled within the context token budget (`MAX_CONTEXT_TOKENS = 1200`).
3. **Single Grounded Generation Call**: The generation model receives only the fresh context and the user's specific question, keeping prompt size predictable and bounded regardless of session length.

```
Session History (Turns 1..N)
     ↓ (Compact Rewriting Prompt: ~200 tokens)
Standalone Search Query (~15 tokens)
     ↓
Vector Retrieval & Re-ranking (Top-K Chunks)
     ↓
Context Injection (Capped at MAX_CONTEXT_TOKENS = 1200 tokens)
     ↓
Final Grounded Answer (~150 tokens)
```

---

## 4. Why Rewritten Queries Must Not Replace Original Messages in the UI

`finee.ai` strictly separates internal retrieval queries from user-facing conversation logs:

```python
# Internal retrieval:
retrieved_chunks = retrieve(query=rewritten_query, k=4)

# UI and Session Memory:
session.history.append({"role": "user", "content": original_user_question})
session.history.append({"role": "assistant", "content": grounded_answer})
```

### Critical Reasons:
1. **User Experience & Trust**: Users expect the chat UI to display verbatim what they typed. If a user asks *"What about the video?"* and the UI alters their message to *"What video explanation is required for project submission?"*, it feels disorienting and artificial.
2. **Compounding Rewriting Errors**: Storing synthetic rewritten queries in history creates artificial user statements that corrupt subsequent turns, causing semantic drift.
3. **Intent Preservation**: The original user prompt captures nuanced phrasing, tone, and specific constraints that must be preserved for compliance audits.

---

## 5. Why Conversational Memory Cannot Replace Fresh Retrieval

It is tempting to rely on LLM memory or past turns to answer follow-up questions without retrieving new chunks. In compliance-grounded financial advisory, this is strictly prohibited:

1. **Document Drift & Expiration**: Compliance policies, fee structures, and interest rates change frequently. Relying on conversational memory rather than fresh vector retrieval risks answering from stale or outdated information.
2. **Attribution & Provenance**: Every factual statement generated by `finee.ai` must cite specific chunk markers (`[1]`, `[2]`). If an answer is generated from conversational memory, citation provenance is lost or fabricated.
3. **Hallucination Amplification**: In multi-turn dialogue, language models tend to agree with user presuppositions. Fresh retrieval grounds every turn in immutable source documents.

---

## 6. The Risk of Rewriting Drift Over Multi-Turn Sessions

Over extended conversations (e.g., 10+ turns), iterative rewriting can suffer from **Rewriting Drift**—the accumulation of irrelevant context anchors from earlier, unrelated topics.

### Drift Mitigation Strategies in `finee.ai`:
1. **Configurable Rolling History Window**: `MAX_CONVERSATION_TURNS = 5` limits context to the 5 most recent turns. Older turns are automatically dropped (FIFO).
2. **Strict Token Ceiling**: `MAX_HISTORY_TOKENS = 1000` prevents bloated dialogue from overwhelming the rewriter.
3. **Rewriting Guardrails & Validation**:
   - `validate_rewritten_query()` rejects outputs that are overly long ($> 350\text{ chars}$), contain multi-paragraph answers, or include AI boilerplate.
   - Temperature is fixed at `0.0` for deterministic, conservative reference resolution.
   - Heuristic fallback ensures graceful operation if the rewriting service fails.

---

## 7. How Safe Refusal Interacts with Multi-Turn Conversations

When a user asks an out-of-domain or unsupported follow-up question within an active conversation:
1. **Query Rewriting**: The rewriter resolves any pronouns based on context.
2. **Retrieval Guardrail Evaluation**: Retrieval returns weak scores ($\text{top\_score} < 0.72$) or empty results.
3. **Pre-LLM Refusal**: The guardrail halts execution **before** invoking the generation LLM, returning `SAFE_REFUSAL_MESSAGE` with `sources: []`.
4. **History Preservation**: The refusal turn is recorded in session history:
   ```json
   {"role": "user", "content": "What is the lunch menu for the Sprint 2 review meeting?"}
   {"role": "assistant", "content": "I don't have enough reliable evidence in the approved knowledge base to answer that question."}
   ```
5. **Session Continuity**: Future turns remain fully functional. If the user subsequent asks an in-domain question, the pipeline resumes normal retrieval and grounded generation without being poisoned by the refusal.

---

## 8. Verification & Test Suite

The conversational RAG system is verified by automated test suites in `tests/test_conversational_rag.py`:
- `test_format_conversation_history`: Verifies dialogue formatting.
- `test_trim_conversation_history_turns`: Verifies turn-based rolling window.
- `test_trim_conversation_history_tokens`: Verifies token ceiling enforcement.
- `test_validate_rewritten_query`: Verifies prefix stripping and answer rejection.
- `test_rewrite_followup_empty_history`: Verifies skipping LLM on initial query.
- `test_conversational_answer_end_to_end`: Verifies full multi-turn conversational workflow.
- `test_conversational_answer_refusal`: Verifies safe refusal on weak retrieval in conversational sessions.
- `test_conversation_session_class`: Verifies session isolation and history state tracking.
