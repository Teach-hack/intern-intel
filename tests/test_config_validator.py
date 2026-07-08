"""Unit tests for the ConfigValidator class."""

from __future__ import annotations

import pytest

from app.core.config_validator import ConfigValidator
from app.core.exceptions import ConfigurationError
from app.core.settings import Settings


def test_validator_valid_config() -> None:
    """Verify that a valid configuration results in no validation errors."""
    valid_dict = {
        "notification": {
            "telegram": True,
            "telegram_bot_token": "123:token",
            "telegram_chat_id": "456",
        },
        "database": {
            "path": "test.db",
        },
        "scheduler": {
            "interval_seconds": 3600,
        },
        "scraper": {
            "timeout": 30,
            "user_agent": "Agent",
        },
        "scrapers": {
            "greenhouse": {
                "board_token": "google",
            },
            "lever": {
                "site_slug": "veriff",
            },
        },
    }
    settings = Settings(settings_dict=valid_dict)
    validator = ConfigValidator()
    result = validator.validate(settings)

    assert result.is_valid is True
    assert len(result.errors) == 0

    # validate_or_raise should not raise
    validator.validate_or_raise(settings)


def test_validator_invalid_database_url() -> None:
    """Verify that an empty database url or missing schema format triggers error."""
    raw_dict = {
        "database": {
            "path": "",
        }
    }
    settings = Settings(settings_dict=raw_dict)
    validator = ConfigValidator()
    result = validator.validate(settings)
    assert result.is_valid is False
    assert any("Database URL" in err for err in result.errors)


def test_validator_invalid_database_url_schema() -> None:
    """Verify database url without prefix triggers format check error."""
    # Settings without path prefix database URL env setup
    with patch_database_url("no_schema_path"):
        settings = Settings(settings_dict={})
        validator = ConfigValidator()
        result = validator.validate(settings)
        assert result.is_valid is False
        assert any("specify driver schema" in err for err in result.errors)


def test_validator_telegram_missing_token_or_chat_id() -> None:
    """Verify validation fails when Telegram notifications are enabled but parameters are missing."""
    raw_dict = {
        "notification": {
            "telegram": True,
            "telegram_bot_token": "",
            "telegram_chat_id": "    ",
        }
    }
    settings = Settings(settings_dict=raw_dict)
    validator = ConfigValidator()
    result = validator.validate(settings)

    assert result.is_valid is False
    assert any("Telegram bot token is required" in err for err in result.errors)
    assert any("Telegram chat ID is required" in err for err in result.errors)


def test_validator_invalid_scheduler_interval() -> None:
    """Verify validation fails when scheduler interval is zero or negative."""
    raw_dict = {
        "scheduler": {
            "interval_seconds": -10,
        }
    }
    settings = Settings(settings_dict=raw_dict)
    validator = ConfigValidator()
    result = validator.validate(settings)

    assert result.is_valid is False
    assert any("Scheduler interval must be positive" in err for err in result.errors)


def test_validator_invalid_scraper_timeout() -> None:
    """Verify validation fails when scraper timeout is negative."""
    raw_dict = {
        "scraper": {
            "timeout": 0,
        }
    }
    settings = Settings(settings_dict=raw_dict)
    validator = ConfigValidator()
    result = validator.validate(settings)

    assert result.is_valid is False
    assert any("Scraper timeout must be positive" in err for err in result.errors)


def test_validator_missing_scraper_configurations() -> None:
    """Verify validation fails when scraper identification fields are empty."""
    raw_dict = {
        "scraper": {
            "user_agent": "   ",
        },
        "scrapers": {
            "greenhouse": {
                "enabled": True,
                "board_token": "",
            },
            "lever": {
                "enabled": True,
                "site_slug": "   ",
            },
        },
    }
    settings = Settings(settings_dict=raw_dict)
    validator = ConfigValidator()
    result = validator.validate(settings)

    assert result.is_valid is False
    assert any("User-Agent must not be empty" in err for err in result.errors)
    assert any(
        "Greenhouse board token must not be empty" in err for err in result.errors
    )
    assert any("Lever site slug must not be empty" in err for err in result.errors)


def test_validator_new_scrapers_validation() -> None:
    """Verify validation of Workday, Ashby, SmartRecruiters, iCIMS, Oracle, and SuccessFactors when enabled."""
    raw_dict = {
        "scraper": {
            "user_agent": "TestBot",
        },
        "scrapers": {
            "greenhouse": {"enabled": False},
            "lever": {"enabled": False},
            "workday": {
                "enabled": True,
                "tenant": "",
                "parent_site_id": "",
            },
            "ashby": {
                "enabled": True,
                "company_id": "   ",
            },
            "smartrecruiters": {
                "enabled": True,
                "company_id": "",
            },
            "icims": {
                "enabled": True,
                "company_id": "",
            },
            "oracle": {
                "enabled": True,
                "company_id": "",
            },
            "successfactors": {
                "enabled": True,
                "company_id": "",
            },
        },
    }
    settings = Settings(settings_dict=raw_dict)
    validator = ConfigValidator()
    result = validator.validate(settings)

    assert result.is_valid is False
    errors_str = "; ".join(result.errors)
    assert "Workday tenant must not be empty" in errors_str
    assert "Workday parent site ID must not be empty" in errors_str
    assert "Ashby company ID must not be empty" in errors_str
    assert "SmartRecruiters company ID must not be empty" in errors_str
    assert "iCIMS company ID must not be empty" in errors_str
    assert "Oracle company ID must not be empty" in errors_str
    assert "SuccessFactors company ID must not be empty" in errors_str


def test_validator_raise_exception() -> None:
    """Verify validate_or_raise propagates ConfigurationError on unhealthy validation."""
    settings = Settings(settings_dict={"scraper": {"timeout": -1}})
    validator = ConfigValidator()
    with pytest.raises(ConfigurationError, match="Configuration validation failed:"):
        validator.validate_or_raise(settings)


def patch_database_url(url: str):
    """Helper to mock DATABASE_URL env var."""
    import os
    from unittest.mock import patch

    return patch.dict(os.environ, {"DATABASE_URL": url})
