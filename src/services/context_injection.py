"""Context Injection and Prompt Augmentation module for finee.ai RAG platform.

Provides standardized chunk source-marker formatting, token-budget calculation and enforcement,
context assembly within model limits, and compliance-grounded augmented prompt construction.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

import tiktoken

from prompts.system import GROUNDED_AUGMENTED_SYSTEM_PROMPT
from src.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_ENCODING = "cl100k_base"
DEFAULT_CHUNK_DELIMITER = "\n\n---\n\n"
NO_CONTEXT_FALLBACK_TEXT = "[No relevant context found in database.]"


class ContextInjectionError(Exception):
    """Base exception for context injection and prompt augmentation."""
    pass


class TokenBudgetExceededError(ContextInjectionError):
    """Raised when token constraints cannot accommodate required minimum instructions."""
    pass


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """Count the number of tokens in a string using tiktoken with fallback.

    Args:
        text: Input string to tokenize.
        encoding_name: tiktoken encoding identifier (default: cl100k_base).

    Returns:
        Integer token count (0 for empty or whitespace-only strings).
    """
    if not text:
        return 0

    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as exc:
        # Documented fallback heuristic if tokenizer encoding fails
        logger.warning("tiktoken encoding '%s' failed (%s); using heuristic token estimation fallback.", encoding_name, exc)
        # Standard estimation: ~4 chars per token for English financial text
        return max(1, len(text) // 4)


def format_chunk(index: int, chunk: Union[Dict[str, Any], Any]) -> str:
    """Format a single retrieved chunk with a standardized citation source marker.

    Source marker syntax:
      - If chunk_index is available: `[{index}] {source}#{chunk_index}`
      - If chunk_index is omitted or None: `[{index}] {source}`

    Format output:
      `[1] client-payment-record.pdf#12`
      `Marcus paid the advisory fee on 20 August.`

    Args:
        index: 1-indexed position of the chunk in the retrieved ranking.
        chunk: Chunk dictionary or object containing text and metadata.

    Returns:
        Formatted multi-line chunk string starting with the source marker.
    """
    if isinstance(chunk, dict):
        text = chunk.get("text", "")
        meta = chunk.get("metadata", {})
    else:
        text = getattr(chunk, "text", "")
        meta = getattr(chunk, "metadata", {})
        if hasattr(meta, "model_dump"):
            meta = meta.model_dump()
        elif not isinstance(meta, dict):
            meta = {}

    source = meta.get("source") or meta.get("document_id") or "source-document"
    chunk_idx = meta.get("chunk_index")
    if chunk_idx is None:
        chunk_idx = meta.get("index")

    if chunk_idx is not None and str(chunk_idx).strip() != "":
        marker = f"[{index}] {source}#{chunk_idx}"
    else:
        marker = f"[{index}] {source}"

    clean_text = text.strip() if isinstance(text, str) else str(text)
    return f"{marker}\n{clean_text}"


def calculate_effective_context_budget(
    max_model_tokens: Optional[int] = None,
    reserved_answer_tokens: Optional[int] = None,
    reserved_instruction_tokens: Optional[int] = None,
    configured_context_tokens: Optional[int] = None,
) -> int:
    """Calculate the safe upper bound for retrieved context tokens dynamically.

    Formula:
      model_ceiling = max_model_tokens - reserved_answer_tokens - reserved_instruction_tokens
      effective_budget = min(configured_context_tokens, model_ceiling)

    Args:
        max_model_tokens: Total model context window (default: settings.MAX_MODEL_CONTEXT_TOKENS).
        reserved_answer_tokens: Output answer token reserve (default: settings.RESERVED_ANSWER_TOKENS).
        reserved_instruction_tokens: System/Question token reserve (default: settings.RESERVED_INSTRUCTION_TOKENS).
        configured_context_tokens: Explicit context budget (default: settings.MAX_CONTEXT_TOKENS).

    Returns:
        Integer token count representing maximum allowable context size.
    """
    m_tokens = max_model_tokens if max_model_tokens is not None else settings.MAX_MODEL_CONTEXT_TOKENS
    ans_tokens = reserved_answer_tokens if reserved_answer_tokens is not None else settings.RESERVED_ANSWER_TOKENS
    inst_tokens = reserved_instruction_tokens if reserved_instruction_tokens is not None else settings.RESERVED_INSTRUCTION_TOKENS
    cfg_tokens = configured_context_tokens if configured_context_tokens is not None else settings.MAX_CONTEXT_TOKENS

    available_space = m_tokens - (ans_tokens + inst_tokens)
    if available_space <= 0:
        logger.warning(
            "Reserved tokens (%d answer + %d instructions) exceed total model context window (%d).",
            ans_tokens,
            inst_tokens,
            m_tokens,
        )
        return max(0, cfg_tokens)

    return max(0, min(cfg_tokens, available_space))


def assemble_context(
    chunks: Sequence[Union[Dict[str, Any], Any]],
    max_context_tokens: Optional[int] = None,
    delimiter: str = DEFAULT_CHUNK_DELIMITER,
    count_fn: Optional[Callable[[str], int]] = None,
) -> Dict[str, Any]:
    """Assemble retrieved chunks into a single formatted context string within token budget.

    Processes chunks in their existing ranking order, formats each with format_chunk(),
    counts tokens, and stops before exceeding max_context_tokens.

    Args:
        chunks: Sequence of candidate chunks ordered by relevance.
        max_context_tokens: Maximum allowed token count for context (default: from settings).
        delimiter: Separator placed between chunks (default: "\\n\\n---\\n\\n").
        count_fn: Optional custom token counting function.

    Returns:
        Dictionary containing:
          - "context": Assembled context string
          - "context_tokens": Number of tokens used
          - "selected_chunks": List of chunks included
          - "sources_used": List of source metadata dicts for citations
          - "source_markers": List of source markers (e.g. ["[1]", "[2]"])
    """
    tok_count = count_fn or count_tokens
    budget = (
        max_context_tokens
        if max_context_tokens is not None
        else calculate_effective_context_budget()
    )

    if not chunks or budget <= 0:
        return {
            "context": "",
            "context_tokens": 0,
            "selected_chunks": [],
            "sources_used": [],
            "source_markers": [],
        }

    formatted_parts: List[str] = []
    selected_chunks: List[Dict[str, Any]] = []
    sources_used: List[Dict[str, Any]] = []
    source_markers: List[str] = []

    for rank_idx, chunk in enumerate(chunks, start=1):
        # 1. Format the chunk with its source marker
        formatted_chunk = format_chunk(rank_idx, chunk)
        chunk_standalone_tokens = tok_count(formatted_chunk)

        # 2. Check if a single individual chunk alone exceeds the total budget
        if chunk_standalone_tokens > budget:
            logger.info(
                "Skipping oversized chunk %d (tokens=%d > budget=%d).",
                rank_idx,
                chunk_standalone_tokens,
                budget,
            )
            continue

        # 3. Calculate new context candidates and projected token usage
        if not formatted_parts:
            projected_context = formatted_chunk
        else:
            projected_context = delimiter.join(formatted_parts + [formatted_chunk])

        projected_tokens = tok_count(projected_context)

        # 4. Stop before exceeding the token budget
        if projected_tokens > budget:
            logger.debug(
                "Context budget reached. Stopping at chunk %d (projected=%d > budget=%d).",
                rank_idx,
                projected_tokens,
                budget,
            )
            break

        # 5. Commit chunk to assembled context
        formatted_parts.append(formatted_chunk)

        # Preserve metadata and chunk structure for citation audit trail
        if isinstance(chunk, dict):
            chunk_copy = dict(chunk)
            meta_copy = dict(chunk.get("metadata", {}))
        else:
            chunk_copy = {
                "text": getattr(chunk, "text", ""),
                "metadata": getattr(chunk, "metadata", {}),
            }
            meta_copy = dict(chunk_copy["metadata"]) if isinstance(chunk_copy["metadata"], dict) else {}

        selected_chunks.append(chunk_copy)
        sources_used.append({
            "marker": f"[{rank_idx}]",
            "source": meta_copy.get("source") or meta_copy.get("document_id") or "source-document",
            "chunk_index": meta_copy.get("chunk_index"),
            "metadata": meta_copy,
            "id": chunk_copy.get("id"),
        })
        source_markers.append(f"[{rank_idx}]")

    assembled_context = delimiter.join(formatted_parts) if formatted_parts else ""
    actual_tokens = tok_count(assembled_context) if assembled_context else 0

    return {
        "context": assembled_context,
        "context_tokens": actual_tokens,
        "selected_chunks": selected_chunks,
        "sources_used": sources_used,
        "source_markers": source_markers,
    }


def build_prompt(
    question: str,
    retrieved_chunks: Sequence[Union[Dict[str, Any], Any]],
    system_instruction: Optional[str] = None,
    max_context_tokens: Optional[int] = None,
    delimiter: str = DEFAULT_CHUNK_DELIMITER,
) -> Dict[str, Any]:
    """Construct a compliance-grounded augmented prompt with strict section separation.

    Sections:
      1. System Instructions (compliance rules, missing evidence fallback, citation markers)
      2. Retrieved Context (delimited, numbered source markers with metadata)
      3. User Question

    Args:
        question: User query or financial question.
        retrieved_chunks: Ranked list of retrieved document chunks.
        system_instruction: Optional override for system grounding prompt.
        max_context_tokens: Optional token ceiling for context assembly.
        delimiter: Separator string between chunks.

    Returns:
        Structured prompt dictionary containing:
          - "prompt": Full unified prompt text
          - "system_instruction": Grounding system instructions
          - "user_prompt": User message containing context and question
          - "context": Assembled context string
          - "context_tokens": Token count of context
          - "selected_chunks": Chunks selected within budget
          - "sources_used": Provenance metadata preserved for citations
          - "source_markers": List of markers (e.g. ["[1]", "[2]"])
          - "question": Cleaned user question string
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")

    cleaned_question = question.strip()
    sys_instruction = (
        system_instruction.strip()
        if system_instruction is not None and system_instruction.strip()
        else GROUNDED_AUGMENTED_SYSTEM_PROMPT.strip()
    )

    # 1. Assemble context within token budget
    assembled = assemble_context(
        chunks=retrieved_chunks,
        max_context_tokens=max_context_tokens,
        delimiter=delimiter,
    )

    context_str = assembled["context"]
    effective_context_display = context_str if context_str else NO_CONTEXT_FALLBACK_TEXT

    # 2. Build user message section
    user_prompt = f"Context:\n{effective_context_display}\n\nQuestion:\n{cleaned_question}"

    # 3. Build unified full prompt text
    full_prompt = f"{sys_instruction}\n\n{user_prompt}"

    return {
        "prompt": full_prompt,
        "system_instruction": sys_instruction,
        "user_prompt": user_prompt,
        "context": context_str,
        "context_tokens": assembled["context_tokens"],
        "selected_chunks": assembled["selected_chunks"],
        "sources_used": assembled["sources_used"],
        "source_markers": assembled["source_markers"],
        "question": cleaned_question,
    }


def format_prompt_overview(prompt_info: Dict[str, Any]) -> str:
    """Format a readable summary of prompt augmentation metrics and citation markers.

    Args:
        prompt_info: Result dictionary returned by build_prompt.

    Returns:
        Formatted multi-line summary string.
    """
    q = prompt_info.get("question", "")
    tokens = prompt_info.get("context_tokens", 0)
    selected = prompt_info.get("selected_chunks", [])
    markers = prompt_info.get("source_markers", [])
    sources = prompt_info.get("sources_used", [])

    lines = [
        "Augmented Prompt Summary",
        "=" * 24,
        f"Question: {q}",
        f"Context Tokens: {tokens}",
        f"Selected Chunks Count: {len(selected)}",
        f"Citation Markers: {', '.join(markers) if markers else 'None'}",
        "",
        "Sources Included:",
        "-" * 20,
    ]

    for s in sources:
        m = s.get("marker", "")
        src = s.get("source", "unknown")
        c_idx = s.get("chunk_index")
        idx_str = f"#{c_idx}" if c_idx is not None else ""
        lines.append(f"  {m} {src}{idx_str}")

    return "\n".join(lines)
