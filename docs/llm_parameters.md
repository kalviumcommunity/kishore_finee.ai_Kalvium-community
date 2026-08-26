# Model Parameters & Output Control for finee.ai

This document provides a concise technical explanation of the LLM generation parameters implemented to control answer formatting, factuality, and costs in the **FInee.ai** RAG platform.

## Parameter Reference

### `temperature`
- **Role**: Controls the randomness/creativity of the model's outputs.
- **Value**: Defaults to `0.1` (Configurable via `LLM_TEMPERATURE`).
- **Description**: As the temperature approaches `0.0`, the model's responses become more deterministic and focused on selecting the most probable tokens. Higher values (e.g., `1.0`) allow for more creative and varied answers.

### `max_tokens`
- **Role**: Imposes a hard limit on the number of generated response tokens.
- **Value**: Defaults to `500` (Configurable via `LLM_MAX_TOKENS`).
- **Description**: Helps prevent uncontrolled and overly verbose generations, reduces costs (since billing is per token), and ensures that responses remain concise.

### `top_p`
- **Role**: Controls nucleus sampling (a technique that limits token generation to a subset of candidates whose cumulative probability is top-P).
- **Value**: Defaults to `1.0` (Configurable via `LLM_TOP_P`).
- **Description**: It is recommended to leave this parameter at its default value and use `temperature` as the primary randomness control. Heavy tuning of both parameters concurrently can produce unpredictable output quality.

### `stop` (Stop Sequences)
- **Role**: Configurable strings that immediately terminate response generation when encountered.
- **Value**: Defaults to `None` (Configurable via `LLM_STOP_SEQUENCES` as a comma-separated list).
- **Description**: Safe parsing handles empty strings, single sequences, and multiple sequences. This is useful for stopping generation if the LLM tries to emit specific markers or exceeds its expected section boundaries.

---

## Why finee.ai Uses Low Temperature

In a **financial advisory compliance system**, correctness is paramount. Advisors rely on the platform to verify facts, compliance regulations, performance figures, and guidelines against approved documents.

- **Factual Grounding**: Lowering the temperature to `0.1` reduces the likelihood of "hallucinations" (the model fabricating figures or facts not present in the retrieved evidence).
- **Output Consistency**: The same query on the same context must yield the same answer every time. High consistency prevents advisor confusion and maintains institutional compliance.
- **Safety Over Style**: The model's primary duty is to accurately report retrieved evidence. Creativity is discouraged; if the information does not exist in the provided source documents, the assistant must state that clearly.
