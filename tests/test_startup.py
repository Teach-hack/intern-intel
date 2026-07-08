"""Unit tests for the Startup initialization class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config_validator import ConfigValidator, ValidationResult
from app.core.exceptions import ConfigurationError
from app.core.settings import Settings
from app.core.startup import Startup
from app.registry import CompanyRegistry


@patch("app.database.migrations.MigrationService")
def test_startup_success_up_to_date(mock_ms_class: MagicMock) -> None:
    """Verify that a successful validation logs summary and returns CompanyRegistry when DB is up to date."""
    mock_ms = mock_ms_class.return_value
    mock_ms.is_up_to_date.return_value = True

    mock_settings = MagicMock(spec=Settings)
    mock_settings.logging_level = "INFO"
    mock_settings.database_url = "sqlite:///test.db"
    mock_settings.database_auto_upgrade = False
    mock_settings.scheduler_interval_seconds = 10
    mock_settings.telegram_enabled = False

    mock_validator = MagicMock(spec=ConfigValidator)
    mock_validator.validate.return_value = ValidationResult(is_valid=True, errors=[])

    startup = Startup(settings=mock_settings, validator=mock_validator)

    with patch("app.core.startup.logger") as mock_logger:
        registry = startup.run()

    assert isinstance(registry, CompanyRegistry)
    mock_validator.validate_or_raise.assert_called_once_with(mock_settings)

    mock_logger.info.assert_any_call(
        "Initializing application startup validation sequence."
    )
    mock_logger.info.assert_any_call("Database schema is up to date.")
    mock_logger.info.assert_any_call("Configuration checks completed successfully.")


@patch("app.database.migrations.MigrationService")
def test_startup_success_auto_upgrade(mock_ms_class: MagicMock) -> None:
    """Verify that startup triggers auto-upgrade if configured."""
    mock_ms = mock_ms_class.return_value
    mock_ms.is_up_to_date.return_value = False

    mock_settings = MagicMock(spec=Settings)
    mock_settings.logging_level = "INFO"
    mock_settings.database_url = "sqlite:///test.db"
    mock_settings.database_auto_upgrade = True
    mock_settings.scheduler_interval_seconds = 10
    mock_settings.telegram_enabled = False

    mock_validator = MagicMock(spec=ConfigValidator)

    startup = Startup(settings=mock_settings, validator=mock_validator)

    with patch("app.core.startup.logger") as mock_logger:
        startup.run()

    mock_ms.upgrade.assert_called_once()
    mock_logger.warning.assert_any_call(
        "Database schema is outdated. Auto-upgrade is enabled. Upgrading now..."
    )


@patch("app.database.migrations.MigrationService")
def test_startup_success_outdated_no_upgrade(mock_ms_class: MagicMock) -> None:
    """Verify that startup warns if outdated but auto-upgrade is False."""
    mock_ms = mock_ms_class.return_value
    mock_ms.is_up_to_date.return_value = False

    mock_settings = MagicMock(spec=Settings)
    mock_settings.logging_level = "INFO"
    mock_settings.database_url = "sqlite:///test.db"
    mock_settings.database_auto_upgrade = False
    mock_settings.scheduler_interval_seconds = 10
    mock_settings.telegram_enabled = False

    mock_validator = MagicMock(spec=ConfigValidator)

    startup = Startup(settings=mock_settings, validator=mock_validator)

    with patch("app.core.startup.logger") as mock_logger:
        startup.run()

    mock_ms.upgrade.assert_not_called()
    mock_logger.warning.assert_any_call(
        "Database schema is behind the latest migration. "
        "Please run 'internintel db upgrade' to apply pending migrations."
    )


def test_startup_failed_validation() -> None:
    """Verify that a failed validation throws ConfigurationError and logs the error."""
    mock_settings = MagicMock(spec=Settings)
    mock_settings.logging_level = "INFO"
    mock_settings.database_url = "sqlite:///test.db"
    mock_settings.scheduler_interval_seconds = 10
    mock_settings.telegram_enabled = False

    mock_validator = MagicMock(spec=ConfigValidator)
    mock_validator.validate_or_raise.side_effect = ConfigurationError(
        "Mocked validation failure"
    )

    startup = Startup(settings=mock_settings, validator=mock_validator)

    with pytest.raises(ConfigurationError, match="Mocked validation failure"):
        startup.run()


def test_startup_dependency_injection_defaults() -> None:
    """Verify default setting container and validator instances are loaded when None."""
    startup = Startup()
    assert isinstance(startup._settings, Settings)
    assert isinstance(startup._validator, ConfigValidator)
