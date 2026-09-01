"""Reusable LLM service layer for compliance-grounded generation."""

import httpx
from typing import Optional, List, Dict, Any
from src.core.config import settings

from prompts import COMPLIANCE_SYSTEM_PROMPT, FINANCIAL_RAG_USER_TEMPLATE, render

class LLMConfigurationError(ValueError):
    """Exception raised when LLM configuration is missing or invalid."""
    pass

class LLMServiceError(Exception):
    """Exception raised when the LLM API call fails."""
    pass

async def generate_answer(
    question: str,
    context: str,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    stop_sequences: Optional[List[str]] = None,
) -> str:
    """Generates a grounded financial answer using the configured LLM API.

    Args:
        question: The user's question.
        context: The retrieved text context/evidence.
        system_instruction: Optional system instruction overriding the default compliance instructions.
        temperature: Optional override for temperature parameter.
        max_tokens: Optional override for max_tokens parameter.
        top_p: Optional override for top_p parameter.
        stop_sequences: Optional override for stop sequences list.

    Returns:
        The generated answer string.

    Raises:
        LLMConfigurationError: If API key is missing.
        LLMServiceError: If the API request fails or returns an error status.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise LLMConfigurationError("OPENAI_API_KEY environment variable is not configured.")

    base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
    model = settings.CHAT_MODEL or "gpt-4o-mini"

    # Resolve generation parameters (use defaults from settings if not overridden)
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
    tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
    tp = top_p if top_p is not None else settings.LLM_TOP_P

    # Resolve stop sequences
    stops = stop_sequences
    if stops is None:
        # Load from parsed stop sequences in config
        stops = settings.parsed_stop_sequences

    # Build instructions using centralized prompt templates
    sys_instruction = system_instruction if system_instruction is not None else COMPLIANCE_SYSTEM_PROMPT
    user_content = render(FINANCIAL_RAG_USER_TEMPLATE, context=context, question=question)

    # Prepare messages
    messages = [
        {"role": "system", "content": sys_instruction},
        {"role": "user", "content": user_content}
    ]

    # Build payload
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temp,
        "max_tokens": tokens,
        "top_p": tp,
    }

    if stops:
        payload["stop"] = stops

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    url = f"{base_url.rstrip('/')}/chat/completions"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                raise LLMServiceError(
                    f"LLM API error (Status {response.status_code}): {response.text}"
                )

            response_data = response.json()
            answer = response_data["choices"][0]["message"]["content"]
            return answer.strip()

    except httpx.RequestError as exc:
        raise LLMServiceError(f"HTTP request to LLM API failed: {exc}")
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMServiceError(f"Unexpected response format from LLM API: {exc}")
