# Metadata Filtering & Hybrid Search

This document details the metadata filtering and hybrid search architecture implemented for the `finee.ai` compliance-grounded financial advisory RAG platform.

---

## 1. Overview & Problem Statement

Similarity search locates document chunks based on semantic proximity in embedding space. However, in enterprise financial advisory and regulatory compliance systems, pure semantic search across an unpartitioned corpus often retrieves plausible but irrelevant chunks from out-of-scope domains (e.g., retrieving enterprise root credential rotation policies when a retail investor asks about client portal password recovery).

**Metadata filtering** scopes retrieval before or during vector search to candidate records matching specific attributes (e.g., `section`, `category`, `user_role`, `document_type`, `effective_date`).

**Hybrid search** augments semantic vector retrieval with lexical keyword scoring to boost chunks containing exact statutory codes, policy IDs, acronyms, or proper names.

```
+-----------------------------------------------------------------------------+
|                                1. USER QUERY                                |
|        "What are the client onboarding rules under SEBI-CIR-2026-42?"       |
+-----------------------------------------------------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
+------------------------------------+   +------------------------------------+
|       DENSE VECTOR SEARCH          |   |       LEXICAL KEYWORD SEARCH       |
|    text-embedding-3-small (1536d)  |   |    Exact Token Matching / BM25     |
|   Scoped by Metadata Pre-filter    |   |     ['sebi-cir-2026-42', 'e-kyc']  |
|  {"category": "compliance"}        |   |                                    |
+------------------------------------+   +------------------------------------+
                   |                                       |
                   | Vector Score: 0.85                    | Keyword Count: 4
                   +-------------------+-------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                           HYBRID RERANKING FORMULA                          |
|         Hybrid Score = (0.8 * Vector Score) + (0.2 * Keyword Score)         |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                          TOP-K GROUNDING CONTEXT                            |
|             Ranked by Hybrid Score with Complete Provenance Meta            |
+-----------------------------------------------------------------------------+
```

---

## 2. Vector Search (Semantic) vs Keyword Search (Lexical)

| Dimension | Vector Search (Semantic) | Keyword Search (Lexical) | Hybrid Search (Combined) |
| :--- | :--- | :--- | :--- |
| **Matching Mechanism** | Cosine similarity in high-dimensional embedding space | Exact term frequency, token overlap, string containment | Weighted linear combination of dense similarity and term hits |
| **Key Strength** | Understands synonyms, paraphrasing, intent, and conceptual similarity | Unmatched accuracy on exact identifiers, regulatory codes, product names | Best of both: semantic understanding with zero-tolerance precision for exact terms |
| **Key Weakness** | Can be misled by high semantic overlap from distractor domains | Fails when query uses synonyms or colloquial phrasing without exact keywords | Requires calibrating weight hyperparameters ($\alpha, \beta$) |
| **Best Use Case** | Conceptual queries: *"How to save tax on investment returns?"* | Exact queries: *"Section 80C limit"*, *"SEBI-CIR-2026-42"* | Real-world advisory queries combining general intent with specific statutory codes |

---

## 3. Metadata Filtering Architecture

### Pre-filtering Mechanism
Both `InMemoryVectorStore` and `ChromaVectorStore` enforce pre-filtering: candidates that do not satisfy the metadata constraints are pruned **prior** to computing expensive distance matrices and sorting:

```python
# InMemoryVectorStore Candidate Filtering
candidates = self._records
if effective_filter:
    candidates = [
        r for r in candidates
        if all(r.metadata.get(k) == v for k, v in effective_filter.items())
    ]
```

### ChromaDB Native Query Filtering
In `ChromaVectorStore`, the dictionary constraints are translated to ChromaDB's native `$and` where-clause:

```python
clean_filter = _sanitize_metadata_for_chroma(effective_filter)
if len(clean_filter) == 1:
    where_clause = clean_filter
elif len(clean_filter) > 1:
    where_clause = {"$and": [{k: v} for k, v in clean_filter.items()]}
```

---

## 4. Hybrid Scoring Formula & Weighting

The combined hybrid score is calculated as:

$$\text{Hybrid Score} = (\omega_{\text{vector}} \times \text{Cosine Similarity}) + (\omega_{\text{keyword}} \times \text{Keyword Score})$$

Where:
- $\omega_{\text{vector}} = 0.8$ (default weight for dense semantic similarity)
- $\omega_{\text{keyword}} = 0.2$ (default weight for lexical keyword frequency)
- $\text{Keyword Score} = \sum_{w \in \text{keywords}} \mathbb{I}(w \in \text{lower}(\text{text}))$

```python
def keyword_score(text: str, keywords: Sequence[str]) -> int:
    """Compute lexical keyword occurrence count in text."""
    if not text or not keywords:
        return 0
    lowered = text.lower()
    return sum(1 for word in keywords if word.lower() in lowered)

def hybrid_rank(
    vector_results: Sequence[Dict[str, Any]],
    keywords: Sequence[str],
    vector_weight: float = 0.8,
    keyword_weight: float = 0.2,
) -> List[Dict[str, Any]]:
    """Combine vector semantic similarity and lexical keyword scoring."""
    ranked = []
    for item in vector_results:
        lexical = keyword_score(item.get("text", ""), keywords)
        vec_score = float(item.get("score", 0.0))
        combined = (vector_weight * vec_score) + (keyword_weight * lexical)
        result_entry = dict(item)
        result_entry["keyword_score"] = lexical
        result_entry["hybrid_score"] = round(combined, 4)
        ranked.append(result_entry)

    ranked.sort(key=lambda item: (item["hybrid_score"], item.get("score", 0.0)), reverse=True)
    for rank_idx, item in enumerate(ranked, start=1):
        item["rank"] = rank_idx
    return ranked
```

---

## 5. Choosing Metadata Filters from Business Needs

Good metadata filters reflect the user persona and regulatory boundary of the inquiry:

- **`section`**: `"Account access"`, `"Section 80C Deductions"`, `"Capital Gains Exemptions"`.
- **`category`**: `"taxation"`, `"regulatory_compliance"`, `"mutual_funds"`, `"account_management"`.
- **`user_role`**: `"retail_investor"`, `"compliance_officer"`, `"wealth_advisor"`, `"internal_employee"`.
- **`department`**: `"client_services"`, `"wealth_advisory"`, `"compliance_office"`.
- **`compliance_code`**: `"SEBI-CIR-2026-42"`, `"RBI-KYC-2025"`.
- **`effective_date`**: Filters out superseded regulations (e.g. `effective_date >= "2026-01-01"`).

---

## 6. Precision vs Recall Trade-offs

| Scenario | Impact on Precision | Impact on Recall | Guidance |
| :--- | :--- | :--- | :--- |
| **Unfiltered Retrieval** | **Lower** — Can return irrelevant chunks with high semantic similarity from wrong departments | **Higher** — Never misses a candidate due to misclassified metadata | Use when query intent spans the entire knowledge base. |
| **Metadata Scoped Retrieval** | **Higher** — Guarantees 100% domain relevance by eliminating cross-domain distractors | **Risk of Lower Recall** — Chunks with missing or mistagged metadata are excluded | Use verified metadata schemas populated during document ingestion. |
| **Hybrid Reranking** | **Highest** — Chunks satisfying semantic meaning AND exact compliance IDs rank #1 | **Optimal** — Retains dense semantic recall while boosting exact keyword matches | Recommended default for all regulatory and financial advisory pipelines. |

---

## 7. Step-by-Step Code Examples

### Filtered Retrieval
```python
from src.retrieval import InMemoryVectorStore, retrieve, show_results

# Unfiltered query (searches entire corpus)
unfiltered = retrieve("What are the password reset steps?", k=3, collection=store)
show_results("Unfiltered", unfiltered)

# Filtered query (scoped to section)
filtered = retrieve(
    "What are the password reset steps?",
    k=3,
    collection=store,
    metadata_filter={"section": "Account access"},
)
show_results("Filtered", filtered)
```

### End-to-End Hybrid Retrieval
```python
from src.retrieval import hybrid_retrieve, show_results

results = hybrid_retrieve(
    query="What are the client onboarding rules under SEBI-CIR-2026-42?",
    keywords=["sebi-cir-2026-42", "e-kyc", "v-cip", "aadhaar"],
    k=3,
    collection=store,
    metadata_filter={"category": "regulatory_compliance"},
    vector_weight=0.8,
    keyword_weight=0.2,
)
show_results("Hybrid Filtered", results)
```

---

## 8. Verification & Execution Output

Run the automated test suite:
```powershell
.\.venv\Scripts\pytest.exe tests/test_metadata_filtering_hybrid.py
```

Run the demonstration script:
```powershell
.\.venv\Scripts\python.exe scripts/demonstrate_filtered_hybrid_search.py
```

All evaluation results are persisted to:
- `outputs/evaluations/metadata_filtering_hybrid_search_results.json`
- `outputs/evaluations/filtered_hybrid_search_demo.json`
