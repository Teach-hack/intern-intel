"""Unit tests for the Alembic MigrationService."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.settings import Settings
from app.database.migrations import MigrationService


@pytest.fixture
def temp_settings(tmp_path: Path) -> Settings:
    """Provide a settings instance pointing to a temporary SQLite database."""
    db_path = tmp_path / "migrations_test.db"
    return Settings({"database": {"path": str(db_path), "url": f"sqlite:///{db_path}"}})


@pytest.fixture
def migration_service(temp_settings: Settings) -> MigrationService:
    """Provide a MigrationService instance configured for the temp DB."""
    return MigrationService(settings=temp_settings)


def test_is_up_to_date_initially_false(migration_service: MigrationService) -> None:
    """A fresh database without migrations is not up to date."""
    assert not migration_service.is_up_to_date()


def test_upgrade_and_is_up_to_date(migration_service: MigrationService) -> None:
    """Running upgrade makes the database up to date."""
    migration_service.upgrade("head")
    assert migration_service.is_up_to_date()


def test_downgrade(migration_service: MigrationService) -> None:
    """Can downgrade database."""
    migration_service.upgrade("head")
    assert migration_service.is_up_to_date()

    # Downgrade to base
    migration_service.downgrade("base")
    assert not migration_service.is_up_to_date()


def test_history_and_current(migration_service: MigrationService) -> None:
    """Can invoke history and current commands without error."""
    migration_service.upgrade("head")

    # These commands print to stdout/stderr via Alembic, so we just ensure they run.
    migration_service.history()
    migration_service.current()


@patch("app.database.migrations.command")
def test_revision_command_delegates(
    mock_command: MagicMock, temp_settings: Settings
) -> None:
    """Verify revision command correctly delegates to Alembic API."""
    service = MigrationService(settings=temp_settings)
    service.revision(message="test revision", autogenerate=True)

    mock_command.revision.assert_called_once()
    kwargs = mock_command.revision.call_args[1]
    assert kwargs["message"] == "test revision"
    assert kwargs["autogenerate"] is True
