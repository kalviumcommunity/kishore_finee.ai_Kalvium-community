"""Unit and integration tests for LLM generation configuration and LLM service."""

import pytest
import os
import httpx
from unittest.mock import patch
from src.core.config import Settings
from src.services.llm import generate_answer, LLMConfigurationError, LLMServiceError


def test_generation_config_defaults():
    """Verify that default generation configuration settings are loaded correctly."""
    settings = Settings()
    # Check that they match the production default specifications
    assert settings.LLM_TEMPERATURE == 0.1
    assert settings.LLM_MAX_TOKENS == 500
    assert settings.LLM_TOP_P == 1.0
    assert settings.LLM_STOP_SEQUENCES is None or settings.LLM_STOP_SEQUENCES == ""
    assert settings.parsed_stop_sequences is None


def test_generation_config_overrides():
    """Verify that environment variables can override generation configuration settings."""
    with patch.dict(
        os.environ,
        {
            "LLM_TEMPERATURE": "0.3",
            "LLM_MAX_TOKENS": "1000",
            "LLM_TOP_P": "0.9",
            "LLM_STOP_SEQUENCES": "stop1,stop2, stop3",
        },
    ):
        custom_settings = Settings()
        assert custom_settings.LLM_TEMPERATURE == 0.3
        assert custom_settings.LLM_MAX_TOKENS == 1000
        assert custom_settings.LLM_TOP_P == 0.9
        assert custom_settings.LLM_STOP_SEQUENCES == "stop1,stop2, stop3"
        # Verify that parsed_stop_sequences is a list of stripped strings
        assert custom_settings.parsed_stop_sequences == ["stop1", "stop2", "stop3"]


def test_stop_sequences_handling_single():
    """Verify that a single stop sequence is handled correctly."""
    with patch.dict(os.environ, {"LLM_STOP_SEQUENCES": "done"}):
        custom_settings = Settings()
        assert custom_settings.parsed_stop_sequences == ["done"]


def test_stop_sequences_handling_empty():
    """Verify that empty stop sequences are handled safely."""
    with patch.dict(os.environ, {"LLM_STOP_SEQUENCES": "  ,  "}):
        custom_settings = Settings()
        assert custom_settings.parsed_stop_sequences is None


@pytest.mark.anyio
async def test_llm_service_missing_api_key():
    """Verify that LLM service raises LLMConfigurationError if API key is missing."""
    with patch("src.services.llm.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        with pytest.raises(LLMConfigurationError) as excinfo:
            await generate_answer(question="Test question", context="Test context")
        assert "OPENAI_API_KEY environment variable is not configured" in str(excinfo.value)


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_llm_service_payload_and_parameters(mock_post):
    """Verify that LLM service sends correct parameters and payload structure to client."""
    # Setup mock response using real httpx.Response object
    mock_post.return_value = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock answer based on retrieved context.",
                    }
                }
            ]
        }
    )

    # Execute service call
    with patch("src.services.llm.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "mocked-api-key"
        mock_settings.OPENAI_BASE_URL = "https://custom-api-url.com/v1"
        mock_settings.CHAT_MODEL = "custom-gpt-model"
        mock_settings.LLM_TEMPERATURE = 0.15
        mock_settings.LLM_MAX_TOKENS = 350
        mock_settings.LLM_TOP_P = 0.95
        mock_settings.parsed_stop_sequences = ["\n", "User:"]

        result = await generate_answer(
            question="What is the AUM?",
            context="Assets Under Management is $1B.",
        )

        assert result == "This is a mock answer based on retrieved context."
        mock_post.assert_called_once()
        
        args, kwargs = mock_post.call_args
        assert args[0] == "https://custom-api-url.com/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer mocked-api-key"
        
        # Verify JSON payload
        json_payload = kwargs["json"]
        assert json_payload["model"] == "custom-gpt-model"
        assert json_payload["temperature"] == 0.15
        assert json_payload["max_tokens"] == 350
        assert json_payload["top_p"] == 0.95
        assert json_payload["stop"] == ["\n", "User:"]
        
        # Check messages and grounding instructions
        messages = json_payload["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "grounding rules" in messages[0]["content"].lower()
        assert messages[1]["role"] == "user"
        assert "What is the AUM?" in messages[1]["content"]


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_llm_service_parameter_overrides(mock_post):
    """Verify that parameter overrides provided to generate_answer function are respected."""
    mock_post.return_value = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"role": "assistant", "content": "Override response"}}]}
    )

    with patch("src.services.llm.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "mocked-api-key"
        mock_settings.OPENAI_BASE_URL = None  # fallback to openai v1
        mock_settings.CHAT_MODEL = None  # fallback to gpt-4o-mini
        mock_settings.LLM_TEMPERATURE = 0.1
        mock_settings.LLM_MAX_TOKENS = 500
        mock_settings.LLM_TOP_P = 1.0
        mock_settings.parsed_stop_sequences = None

        await generate_answer(
            question="Question?",
            context="Context.",
            temperature=0.0,
            max_tokens=100,
            top_p=0.5,
            stop_sequences=["STOP"],
        )

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.openai.com/v1/chat/completions"
        
        json_payload = kwargs["json"]
        assert json_payload["model"] == "gpt-4o-mini"
        assert json_payload["temperature"] == 0.0
        assert json_payload["max_tokens"] == 100
        assert json_payload["top_p"] == 0.5
        assert json_payload["stop"] == ["STOP"]


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_llm_service_api_failure(mock_post):
    """Verify that LLM service raises LLMServiceError on non-200 API response."""
    mock_post.return_value = httpx.Response(
        status_code=401,
        content=b"Unauthorized"
    )

    with patch("src.services.llm.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "invalid-key"
        mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"
        mock_settings.CHAT_MODEL = "gpt-4o-mini"

        with pytest.raises(LLMServiceError) as excinfo:
            await generate_answer(question="Question?", context="Context.")
        assert "LLM API error (Status 401): Unauthorized" in str(excinfo.value)
