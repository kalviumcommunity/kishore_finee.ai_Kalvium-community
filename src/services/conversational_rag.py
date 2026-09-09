"""Conversational RAG and Follow-up Query Rewriting module for finee.ai.

Provides conversation history tracking, rolling token/turn limits, follow-up query
rewriting into standalone search queries, and integration with guarded RAG retrieval.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence, Union
import uuid

import httpx

from prompts.system import QUERY_REWRITE_SYSTEM_PROMPT, QUERY_REWRITE_USER_TEMPLATE
from src.core.config import settings
from src.services.context_injection import count_tokens
from src.services.guardrails import evaluate_retrieval_strength, guarded_answer

logger = logging.getLogger(__name__)


def format_conversation_history(history: Sequence[Dict[str, str]]) -> str:
    """Format structured conversation history messages into a clean readable dialogue string.

    Args:
        history: Sequence of message dicts containing 'role' ('user'|'assistant') and 'content'.

    Returns:
        Formatted multi-line dialogue string.
    """
    if not history:
        return "[No prior conversation history]"

    lines: List[str] = []
    for msg in history:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "").strip()
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


def trim_conversation_history(
    history: Sequence[Dict[str, str]],
    max_turns: Optional[int] = None,
    max_tokens: Optional[int] = None,
) -> List[Dict[str, str]]:
    """Trim conversation history to stay within maximum turn counts and token budget.

    Args:
        history: Complete sequence of conversation messages.
        max_turns: Maximum number of recent user/assistant turns (default: settings.MAX_CONVERSATION_TURNS).
        max_tokens: Maximum token ceiling for history (default: settings.MAX_HISTORY_TOKENS).

    Returns:
        Trimmed list of recent message dictionaries.
    """
    if not history:
        return []

    turns_limit = max_turns if max_turns is not None else settings.MAX_CONVERSATION_TURNS
    token_budget = max_tokens if max_tokens is not None else settings.MAX_HISTORY_TOKENS

    # 1. Turn-based rolling window (each turn comprises up to 2 messages: user + assistant)
    max_messages = max(1, turns_limit * 2)
    trimmed: List[Dict[str, str]] = [dict(m) for m in history[-max_messages:]]

    # 2. Token-budget enforcement
    def calc_history_tokens(msgs: List[Dict[str, str]]) -> int:
        return sum(count_tokens(m.get("content", "")) for m in msgs)

    while len(trimmed) > 1 and calc_history_tokens(trimmed) > token_budget:
        # Pop oldest message
        trimmed.pop(0)

    return trimmed


def validate_rewritten_query(rewritten: str, original_question: str) -> str:
    """Validate and sanitize the rewritten query string returned by the model.

    Rules:
      - Strips extraneous prefixes ('Query:', 'Standalone Search Query:').
      - Strips surrounding quotes and markdown formatting.
      - Rejects outputs that are empty, multi-paragraph answers, or error messages.
      - Falls back safely to original_question upon validation failure.

    Args:
        rewritten: Raw string returned by query rewriting model.
        original_question: The original user question.

    Returns:
        Sanitized standalone query string.
    """
    if not rewritten or not isinstance(rewritten, str):
        return original_question.strip()

    cleaned = rewritten.strip()

    # Remove code blocks or formatting if present
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```$", "", cleaned)

    # Strip common label prefixes (case-insensitive)
    cleaned = re.sub(
        r"^(?:Standalone\s+Search\s+Query|Standalone\s+Query|Search\s+Query|Rewritten\s+Query|Rewritten\s+Question|Query):\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # Strip surrounding quotes
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    # Validate output is a query, not a lengthy multi-paragraph answer or error
    if not cleaned:
        return original_question.strip()

    # If the output contains multiple line breaks or exceeds 300 characters, it likely answered instead of rewriting
    if cleaned.count("\n") > 2 or len(cleaned) > 350:
        logger.warning(
            "Rewritten query rejected (too verbose or structured like an answer): '%s'. Using fallback.",
            cleaned[:80],
        )
        return original_question.strip()

    # Check for hallucinated AI boilerplate
    if cleaned.lower().startswith("as an ai") or cleaned.lower().startswith("based on"):
        return original_question.strip()

    return cleaned


def _heuristic_query_rewrite(history: Sequence[Dict[str, str]], question: str) -> str:
    """Deterministic reference resolution heuristic for offline testing or fallback.

    Extracts recent topic keywords from prior conversation turns to resolve pronouns.

    Args:
        history: Sequence of prior conversation messages.
        question: User follow-up question.

    Returns:
        Rewritten query string.
    """
    q_clean = question.strip()
    if not history:
        return q_clean

    q_lower = q_clean.lower()
    last_user_msg = ""
    last_assistant_msg = ""

    for m in reversed(history):
        if m.get("role") == "user" and not last_user_msg:
            last_user_msg = m.get("content", "")
        elif m.get("role") == "assistant" and not last_assistant_msg:
            last_assistant_msg = m.get("content", "")

    # Extract salient context anchor from last user turn
    context_anchor = last_user_msg.strip(" ?.")
    # Clean leading interrogative prefixes if the previous turn was a question
    cleaned_anchor = re.sub(
        r"^(?:what|how|why|when|where|is|are|does|do)\s+(?:evidence\s+(?:is\s+)?required\s+for\s+|is\s+required\s+for\s+|about\s+)?",
        "",
        context_anchor,
        flags=re.IGNORECASE,
    ).strip()
    cleaned_anchor = re.sub(r"^the\s+", "", cleaned_anchor, flags=re.IGNORECASE).strip()
    anchor_label = cleaned_anchor if cleaned_anchor else context_anchor

    # 1. Pronoun / follow-up resolution patterns
    if re.match(r"^what about (the\s+)?", q_lower):
        topic = re.sub(r"^what about (the\s+)?", "", q_clean, flags=re.IGNORECASE).rstrip(" ?.")
        topic_desc = f"{topic} explanation" if topic.lower() == "video" else topic
        return f"What {topic_desc} is required for {anchor_label}?"

    if "does it apply to" in q_lower or "is it applicable to" in q_lower:
        match = re.search(r"(?:does it apply to|is it applicable to)\s+(.*)", q_clean, re.IGNORECASE)
        target = match.group(1).rstrip(" ?.") if match else "this"
        return f"Does the {anchor_label} requirement apply to {target}?"

    if re.search(r"\b(it|that|this|they|them)\b", q_lower) and anchor_label:
        # If question contains ambiguous pronoun, append context anchor
        return f"{q_clean.rstrip(' ?.')} regarding {anchor_label}?"

    return q_clean


async def rewrite_followup(
    history: Sequence[Dict[str, str]],
    question: str,
    model: Optional[str] = None,
    timeout: float = 10.0,
) -> str:
    """Rewrite a conversational follow-up question into an unambiguous standalone search query.

    Uses conversation history only to resolve references and pronouns. Does not answer
    the question or invent unsupported facts.

    Args:
        history: List of previous conversation messages.
        question: Latest user question.
        model: Optional model override (default: settings.QUERY_REWRITE_MODEL or settings.CHAT_MODEL).
        timeout: HTTP request timeout in seconds.

    Returns:
        Clean standalone query string ready for vector retrieval.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")

    cleaned_q = question.strip()

    # If no history exists, question is already standalone; skip LLM call
    if not history:
        return cleaned_q

    trimmed_history = trim_conversation_history(history)
    if not trimmed_history:
        return cleaned_q

    # Check API key configuration
    api_key = settings.OPENAI_API_KEY or settings.GROQ_API_KEY
    base_url = settings.OPENAI_BASE_URL or settings.GROQ_BASE_URL or "https://api.openai.com/v1"
    target_model = model or settings.QUERY_REWRITE_MODEL or settings.CHAT_MODEL or "gpt-4o-mini"

    # If no API key configured, use deterministic heuristic resolver
    if not api_key or not str(api_key).strip():
        return _heuristic_query_rewrite(trimmed_history, cleaned_q)

    # Build prompt
    hist_text = format_conversation_history(trimmed_history)
    user_prompt = QUERY_REWRITE_USER_TEMPLATE.format(history=hist_text, question=cleaned_q)

    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": QUERY_REWRITE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 100,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = f"{base_url.rstrip('/')}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                raw_rewritten = data["choices"][0]["message"]["content"]
                return validate_rewritten_query(raw_rewritten, cleaned_q)
            else:
                logger.warning(
                    "LLM query rewriting returned status %d: %s. Using heuristic fallback.",
                    resp.status_code,
                    resp.text,
                )
                return _heuristic_query_rewrite(trimmed_history, cleaned_q)
    except Exception as exc:
        logger.warning("LLM query rewriting failed (%s). Using heuristic fallback.", exc)
        return _heuristic_query_rewrite(trimmed_history, cleaned_q)


async def conversational_answer(
    history: List[Dict[str, str]],
    user_question: str,
    collection: Optional[Any] = None,
    chunks: Optional[Sequence[Union[Dict[str, Any], Any]]] = None,
    min_top_score: Optional[float] = None,
    min_supporting_chunks: Optional[int] = None,
    top_k: Optional[int] = None,
    use_reranker: Optional[bool] = None,
    refusal_message: Optional[str] = None,
    model: Optional[str] = None,
    **llm_kwargs,
) -> Dict[str, Any]:
    """Execute end-to-end Conversational RAG with follow-up query rewriting and guardrails.

    Flow:
      1. Read recent conversation history.
      2. Rewrite follow-up into a standalone retrieval query.
      3. Retrieve candidate chunks using the REWRITTEN query.
      4. Re-rank candidates (if enabled).
      5. Apply retrieval-strength guardrails.
      6. If weak: return safe refusal without LLM answer call.
      7. If strong: generate grounded answer for the ORIGINAL user question.
      8. Append user and assistant turns to conversation history.

    Args:
        history: Mutable list of conversation message dicts.
        user_question: Latest user question.
        collection: Vector store collection to query against.
        chunks: Optional pre-retrieved candidate chunks.
        min_top_score: Guardrail top score threshold.
        min_supporting_chunks: Guardrail supporting count threshold.
        top_k: Candidate retrieval count.
        use_reranker: Toggle re-ranking.
        refusal_message: Refusal message override.
        model: Query rewriting / generation model override.

    Returns:
        Structured response dictionary with answer, sources, rewritten_query, status, and history.
    """
    if not isinstance(user_question, str) or not user_question.strip():
        raise ValueError("Question must be a non-empty string.")

    cleaned_q = user_question.strip()
    k_val = top_k if top_k is not None else settings.RETRIEVAL_TOP_K

    # 1. Rewrite follow-up query using conversation history
    rewritten_query = await rewrite_followup(
        history=history,
        question=cleaned_q,
        model=model,
    )

    # 2. Retrieve candidate chunks using the REWRITTEN query (not the ambiguous follow-up)
    if chunks is not None:
        retrieved_candidates = list(chunks)
    elif collection is not None:
        from src.retrieval.retriever import retrieve
        retrieved_candidates = retrieve(query=rewritten_query, k=k_val, collection=collection)
    else:
        retrieved_candidates = []

    # 3. Apply guarded answer pipeline on the ORIGINAL user question
    guard_res = await guarded_answer(
        question=cleaned_q,
        chunks=retrieved_candidates,
        min_top_score=min_top_score,
        min_supporting_chunks=min_supporting_chunks,
        top_k=k_val,
        use_reranker=use_reranker,
        refusal_message=refusal_message,
        **llm_kwargs,
    )

    # 4. Append user and assistant messages to history (store actual user question, NOT rewritten query)
    history.append({"role": "user", "content": cleaned_q})
    history.append({"role": "assistant", "content": guard_res["answer"]})

    # Keep stored history within configured rolling limits
    trimmed_active_history = trim_conversation_history(history)
    history.clear()
    history.extend(trimmed_active_history)

    return {
        "rewritten_query": rewritten_query,
        "original_question": cleaned_q,
        "answer": guard_res["answer"],
        "sources": guard_res["sources"],
        "status": guard_res["status"],
        "refusal_reason": guard_res.get("refusal_reason"),
        "metrics": {
            **guard_res.get("metrics", {}),
            "rewritten": rewritten_query != cleaned_q,
            "history_turns": len(history) // 2,
        },
        "history": list(history),
        "prompt_info": guard_res.get("prompt_info"),
        "context": guard_res.get("context"),
        "context_tokens": guard_res.get("context_tokens", 0),
        "selected_chunks": guard_res.get("selected_chunks", []),
        "source_markers": guard_res.get("source_markers", []),
    }


class ConversationSession:
    """Encapsulates session-isolated conversational RAG state and history."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        collection: Optional[Any] = None,
        max_turns: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        """Initialize an isolated conversation session.

        Args:
            session_id: Optional unique session identifier.
            collection: Vector store collection to query against.
            max_turns: Maximum rolling turns retained in history.
            max_tokens: Maximum token budget for history.
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.collection = collection
        self.max_turns = max_turns or settings.MAX_CONVERSATION_TURNS
        self.max_tokens = max_tokens or settings.MAX_HISTORY_TOKENS
        self._history: List[Dict[str, str]] = []

    @property
    def history(self) -> List[Dict[str, str]]:
        """Return a copy of current conversation history."""
        return list(self._history)

    def clear(self) -> None:
        """Clear session conversation history."""
        self._history.clear()

    async def ask(
        self,
        question: str,
        collection: Optional[Any] = None,
        chunks: Optional[Sequence[Union[Dict[str, Any], Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send a conversational turn, rewrite query, retrieve evidence, and generate response.

        Args:
            question: User question or follow-up.
            collection: Optional vector store collection override.
            chunks: Optional pre-retrieved candidate chunks.

        Returns:
            Structured response dictionary.
        """
        target_collection = collection if collection is not None else self.collection
        return await conversational_answer(
            history=self._history,
            user_question=question,
            collection=target_collection,
            chunks=chunks,
            **kwargs,
        )
