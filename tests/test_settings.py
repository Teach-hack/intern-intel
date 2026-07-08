"""Unit tests for the strongly typed Settings class."""

from __future__ import annotations

import os
from unittest.mock import patch

from app.core.settings import Settings


def test_settings_default_values() -> None:
    """Verify that settings are loaded with correct defaults when empty."""
    # Ensure environment variables are clear
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings(settings_dict={})

        assert settings.telegram_enabled is False
        assert settings.telegram_bot_token is None
        assert settings.telegram_chat_id is None
        assert settings.database_url == "sqlite:///data/database/internships.db"
        assert settings.scheduler_interval_seconds == 3600
        assert settings.logging_level == "INFO"
        assert settings.scraper_timeout == 30
        assert settings.scraper_user_agent == "InternIntelBot/1.0"
        assert settings.http_follow_redirects is True
        assert settings.greenhouse_board_token == "google"
        assert settings.lever_site_slug == "veriff"


def test_settings_dict_overrides() -> None:
    """Verify that custom dictionary values override defaults."""
    raw_dict = {
        "notification": {
            "telegram": True,
            "telegram_bot_token": "token123",
            "telegram_chat_id": "chat123",
        },
        "database": {
            "path": "custom.db",
        },
        "scheduler": {
            "interval_seconds": 1800,
        },
        "logging": {
            "level": "DEBUG",
        },
        "scraper": {
            "timeout": 45,
            "user_agent": "CustomAgent/2.0",
        },
        "http": {
            "follow_redirects": False,
        },
        "scrapers": {
            "greenhouse": {
                "board_token": "custom-greenhouse",
            },
            "lever": {
                "site_slug": "custom-lever",
            },
        },
    }

    settings = Settings(settings_dict=raw_dict)

    assert settings.telegram_enabled is True
    assert settings.telegram_bot_token == "token123"
    assert settings.telegram_chat_id == "chat123"
    assert settings.database_url == "sqlite:///custom.db"
    assert settings.scheduler_interval_seconds == 1800
    assert settings.logging_level == "DEBUG"
    assert settings.scraper_timeout == 45
    assert settings.scraper_user_agent == "CustomAgent/2.0"
    assert settings.http_follow_redirects is False
    assert settings.greenhouse_board_token == "custom-greenhouse"
    assert settings.lever_site_slug == "custom-lever"


def test_settings_env_overrides() -> None:
    """Verify that environment variables take precedence over config dictionary."""
    raw_dict = {
        "scheduler": {
            "interval_seconds": 1800,
        },
        "database": {
            "path": "custom.db",
        },
    }

    env_vars = {
        "TELEGRAM_ENABLED": "true",
        "TELEGRAM_BOT_TOKEN": "env-token",
        "TELEGRAM_CHAT_ID": "env-chat",
        "DATABASE_URL": "postgresql://user:pass@host/db",
        "SCHEDULER_INTERVAL_SECONDS": "900",
        "LOGGING_LEVEL": "WARNING",
        "SCRAPER_TIMEOUT": "15",
        "SCRAPER_USER_AGENT": "EnvAgent",
        "HTTP_FOLLOW_REDIRECTS": "false",
        "GREENHOUSE_BOARD_TOKEN": "env-greenhouse",
        "LEVER_SITE_SLUG": "env-lever",
    }

    with patch.dict(os.environ, env_vars):
        settings = Settings(settings_dict=raw_dict)

        assert settings.telegram_enabled is True
        assert settings.telegram_bot_token == "env-token"
        assert settings.telegram_chat_id == "env-chat"
        assert settings.database_url == "postgresql://user:pass@host/db"
        assert settings.scheduler_interval_seconds == 900
        assert settings.logging_level == "WARNING"
        assert settings.scraper_timeout == 15
        assert settings.scraper_user_agent == "EnvAgent"
        assert settings.http_follow_redirects is False
        assert settings.greenhouse_board_token == "env-greenhouse"
        assert settings.lever_site_slug == "env-lever"


def test_settings_invalid_integer_conversions() -> None:
    """Verify that invalid/non-integer strings fall back to defaults gracefully."""
    raw_dict = {
        "scheduler": {"interval_seconds": "invalid_int"},
        "scraper": {"timeout": "invalid_timeout"},
    }

    settings = Settings(settings_dict=raw_dict)
    assert settings.scheduler_interval_seconds == 3600
    assert settings.scraper_timeout == 30


def test_settings_database_url_from_raw_url() -> None:
    """Verify that database_url returns direct raw URL if configured with schema prefix."""
    raw_dict = {
        "database": {
            "path": "sqlite:////absolute/path/to/db.sqlite",
        }
    }
    settings = Settings(settings_dict=raw_dict)
    assert settings.database_url == "sqlite:////absolute/path/to/db.sqlite"


def test_settings_reload() -> None:
    """Verify that reload parses configuration settings from disk again."""
    settings = Settings(settings_dict={"test": "old"})
    with patch.object(settings, "_load_yaml_config", return_value={"test": "new"}):
        settings.reload()
        assert settings.get("test") == "new"
