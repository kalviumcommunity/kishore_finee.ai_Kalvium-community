"""Unit tests for configuration system and environment loading."""

import os
from unittest.mock import patch
from src.core.config import Settings, get_settings


def test_default_settings():
    """Verify default configuration settings."""
    settings = Settings()
    assert settings.APP_NAME == "Financial Advisory RAG Platform"
    assert settings.APP_ENV in ["development", "staging", "production", "testing"]
    assert settings.APP_HOST == "0.0.0.0"
    assert settings.APP_PORT == 8000
    assert settings.LOG_LEVEL == "INFO"
    assert not settings.is_production


def test_environment_override():
    """Verify that environment variables safely override defaults."""
    with patch.dict(
        os.environ,
        {
            "APP_NAME": "Custom Financial RAG",
            "APP_ENV": "production",
            "APP_PORT": "9000",
            "LOG_LEVEL": "DEBUG",
        },
    ):
        custom_settings = Settings()
        assert custom_settings.APP_NAME == "Custom Financial RAG"
        assert custom_settings.APP_ENV == "production"
        assert custom_settings.APP_PORT == 9000
        assert custom_settings.LOG_LEVEL == "DEBUG"
        assert custom_settings.is_production
        assert not custom_settings.is_development


def test_get_settings_cached():
    """Verify that get_settings provides a cached singleton."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
