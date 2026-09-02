# Prompts & Reusable Prompt Design

This directory houses centralized, reusable prompt templates and compliance system prompts for the **FInee.ai** financial advisory RAG platform.

## Why Centralized Prompt Templates?

- **Zero Inline Prompt Drift**: Modifying grounding rules or citation requirements in a single place automatically updates all consuming features (Chat endpoints, batch evaluators, CLI tools).
- **Decoupled Business Logic**: Prompt definitions remain separate from application and service logic.
- **Runtime Validation**: Ensures dynamic variables (`{context}`, `{question}`, etc.) are injected and prevents missing placeholders.

---

## File Structure

```text
prompts/
├── __init__.py         # Package exports for clean imports
├── templates.py        # Core PromptTemplate class and render() function
├── answer.py           # QA and grounded answer templates (ANSWER, CITATION_ANSWER_TEMPLATE, etc.)
├── system.py           # Compliance guardrails and system instructions
└── README.md           # Documentation and usage guide
```

---

## Usage Examples

### 1. Basic String Template Rendering

```python
from prompts.answer import ANSWER, render

# Render the standard QA template with runtime variables
prompt = render(
    ANSWER,
    context="Apex Horizon Fund (Class A) 2025 return: 9.85%.",
    question="What was the return of Apex Horizon Fund in 2025?",
)
```

### 2. Using `PromptTemplate` with Automatic Validation

```python
from prompts.templates import PromptTemplate

custom_template = PromptTemplate(
    template="Client: {client_name}\nPortfolio: {portfolio_id}\nQuery: {query}",
    name="client_portfolio_query",
)

# Renders cleanly or raises PromptTemplateError if any variable is missing
prompt_text = custom_template.render(
    client_name="Jane Doe",
    portfolio_id="PORT-9012",
    query="Review risk distribution",
)
```

### 3. Reusing Templates Across Multiple Features

```python
from prompts import ANSWER, render

# 1. In API Chat Endpoint
chat_prompt = render(ANSWER, context=retrieved_chunks, question=user_question)

# 2. In Batch Evaluator
eval_prompts = [
    render(ANSWER, context=item["context"], question=item["question"])
    for item in test_dataset
]

# 3. In CLI Tool
cli_prompt = render(ANSWER, context=cli_context, question=cli_query)
```

---

## Running the Demonstration

Execute the demonstration script to view interactive outputs:

```bash
python -m scripts.prompt_template_demo
```
