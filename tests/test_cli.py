"""Unit tests for the argparse CLI interface class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.cli import CLI, main
from app.notifications.notification_service import NotificationService
from app.runner import Runner
from app.services.database_service import DatabaseService


@pytest.fixture
def mock_runner() -> MagicMock:
    """Fixture to provide a mocked Runner."""
    return MagicMock(spec=Runner)


@pytest.fixture
def mock_database_service() -> MagicMock:
    """Fixture to provide a mocked DatabaseService."""
    return MagicMock(spec=DatabaseService)


@pytest.fixture
def mock_notification_service() -> MagicMock:
    """Fixture to provide a mocked NotificationService."""
    return MagicMock(spec=NotificationService)


def test_cli_initialization_defaults() -> None:
    """Verify default initialization of the CLI."""
    cli = CLI()
    assert isinstance(cli._runner, Runner)
    assert isinstance(cli._database_service, DatabaseService)
    assert cli._notification_service is None


def test_cli_dependency_injection(
    mock_runner: MagicMock,
    mock_database_service: MagicMock,
    mock_notification_service: MagicMock,
) -> None:
    """Verify correct dependency injection on CLI init."""
    cli = CLI(
        runner=mock_runner,
        database_service=mock_database_service,
        notification_service=mock_notification_service,
    )
    assert cli._runner is mock_runner
    assert cli._database_service is mock_database_service
    assert cli._notification_service is mock_notification_service


def test_cli_run_command(mock_runner: MagicMock) -> None:
    """Verify run command invokes runner.run()."""
    cli = CLI(runner=mock_runner)
    with patch("app.cli.logger") as mock_logger:
        exit_code = cli.execute(["run"])

    assert exit_code == 0
    mock_runner.run.assert_called_once()
    mock_logger.info.assert_called_once_with("Executing CLI 'run' command.")


def test_cli_scrape_command(mock_runner: MagicMock) -> None:
    """Verify scrape command invokes runner run but overrides notifier."""
    cli = CLI(runner=mock_runner)
    mock_runner._pipeline_service = MagicMock()
    with patch("app.cli.logger") as mock_logger:
        with patch("app.cli.Runner") as mock_runner_class:
            mock_runner_instance = MagicMock()
            mock_runner_class.return_value = mock_runner_instance

            exit_code = cli.execute(["scrape"])

    assert exit_code == 0
    mock_logger.info.assert_called_once_with("Executing CLI 'scrape' command.")
    mock_runner_class.assert_called_once()

    # The constructed runner should have had a NotificationService with no notifier
    _, kwargs = mock_runner_class.call_args
    ns = kwargs["notification_service"]
    assert isinstance(ns, NotificationService)
    assert ns._notifier is None
    mock_runner_instance.run.assert_called_once()


def test_cli_notify_command_no_jobs(
    mock_database_service: MagicMock,
    mock_notification_service: MagicMock,
) -> None:
    """Verify notify command exits early with no jobs in DB."""
    mock_database_service.get_all.return_value = []
    cli = CLI(
        database_service=mock_database_service,
        notification_service=mock_notification_service,
    )

    with patch("app.cli.logger") as mock_logger:
        exit_code = cli.execute(["notify"])

    assert exit_code == 0
    mock_database_service.get_all.assert_called_once()
    mock_notification_service.notify_many.assert_not_called()
    mock_logger.info.assert_any_call("Executing CLI 'notify' command.")
    mock_logger.info.assert_any_call("No internships found in database to notify.")


def test_cli_notify_command_with_jobs(
    mock_database_service: MagicMock,
    mock_notification_service: MagicMock,
) -> None:
    """Verify notify command calls notify_many with found DB listings."""
    jobs = [MagicMock()]
    mock_database_service.get_all.return_value = jobs
    cli = CLI(
        database_service=mock_database_service,
        notification_service=mock_notification_service,
    )

    with patch("app.cli.logger") as mock_logger:
        exit_code = cli.execute(["notify"])

    assert exit_code == 0
    mock_database_service.get_all.assert_called_once()
    mock_notification_service.notify_many.assert_called_once_with(jobs)
    mock_logger.info.assert_called_once_with("Executing CLI 'notify' command.")


def test_cli_scheduler_command(mock_runner: MagicMock) -> None:
    """Verify scheduler command runs the scheduler forever."""
    cli = CLI(runner=mock_runner)

    with patch("app.cli.settings") as mock_settings:
        mock_settings.get.return_value = 10
        with patch("app.cli.Scheduler") as mock_scheduler_class:
            mock_scheduler_instance = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler_instance

            with patch("app.cli.logger") as mock_logger:
                exit_code = cli.execute(["scheduler"])

    assert exit_code == 0
    mock_logger.info.assert_called_once_with("Executing CLI 'scheduler' command.")
    mock_scheduler_class.assert_called_once_with(
        runner=mock_runner, interval_seconds=10
    )
    mock_scheduler_instance.run_forever.assert_called_once()


def test_cli_version_command() -> None:
    """Verify version command prints version string from settings."""
    cli = CLI()
    with patch("app.cli.settings") as mock_settings:
        mock_settings.get.return_value = "1.2.3"
        with patch("builtins.print") as mock_print:
            exit_code = cli.execute(["version"])

    assert exit_code == 0
    mock_print.assert_called_once_with("InternIntel v1.2.3")


def test_cli_doctor_healthy() -> None:
    """Verify doctor command outputs OK when everything is configured correctly."""
    cli = CLI()
    with patch("app.cli.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: {
            "database.path": "test.db",
            "notification.telegram": True,
            "notification.telegram_bot_token": "token",
            "notification.telegram_chat_id": "chat",
        }.get(key, default)

        with patch("builtins.print") as mock_print:
            exit_code = cli.execute(["doctor"])

    assert exit_code == 0
    mock_settings.reload.assert_called_once()
    mock_print.assert_any_call("[OK] Configuration load successful.")
    mock_print.assert_any_call("[OK] Database path configured: test.db")
    mock_print.assert_any_call("[OK] Telegram settings configured.")


def test_cli_doctor_failed_config() -> None:
    """Verify doctor command returns non-zero code on configuration reload error."""
    cli = CLI()
    with patch("app.cli.settings") as mock_settings:
        mock_settings.reload.side_effect = ValueError("Corrupt file")

        with patch("builtins.print") as mock_print:
            exit_code = cli.execute(["doctor"])

    assert exit_code == 1
    mock_print.assert_any_call("[ERROR] Failed to load configuration: Corrupt file")


def test_cli_doctor_missing_database() -> None:
    """Verify doctor command returns non-zero code when database path is missing."""
    cli = CLI()
    with patch("app.cli.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: {
            "database.path": None,
        }.get(key, default)

        with patch("builtins.print") as mock_print:
            exit_code = cli.execute(["doctor"])

    assert exit_code == 1
    mock_print.assert_any_call("[ERROR] Database path is not configured.")


def test_cli_doctor_telegram_warn() -> None:
    """Verify doctor prints warning if telegram notification is enabled but missing credentials."""
    cli = CLI()
    with patch("app.cli.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: {
            "database.path": "test.db",
            "notification.telegram": True,
            "notification.telegram_bot_token": "",
            "notification.telegram_chat_id": "",
        }.get(key, default)

        with patch("builtins.print") as mock_print:
            exit_code = cli.execute(["doctor"])

    assert exit_code == 0
    mock_print.assert_any_call(
        "[WARN] Telegram enabled but token or chat ID is missing."
    )


def test_cli_invalid_command() -> None:
    """Verify that invalid arguments raise SystemExit via argparse."""
    cli = CLI()
    with pytest.raises(SystemExit):
        cli.execute(["invalid"])


def test_cli_db_upgrade() -> None:
    """Verify db upgrade command delegates to MigrationService."""
    cli = CLI()
    with patch.object(cli, "_get_migration_service") as mock_get_ms:
        ms = mock_get_ms.return_value
        exit_code = cli.execute(["db", "upgrade", "head"])
    assert exit_code == 0
    ms.upgrade.assert_called_once_with("head")


def test_cli_db_downgrade() -> None:
    """Verify db downgrade command delegates to MigrationService."""
    cli = CLI()
    with patch.object(cli, "_get_migration_service") as mock_get_ms:
        ms = mock_get_ms.return_value
        exit_code = cli.execute(["db", "downgrade", "base"])
    assert exit_code == 0
    ms.downgrade.assert_called_once_with("base")


def test_cli_db_current() -> None:
    """Verify db current command delegates to MigrationService."""
    cli = CLI()
    with patch.object(cli, "_get_migration_service") as mock_get_ms:
        ms = mock_get_ms.return_value
        exit_code = cli.execute(["db", "current"])
    assert exit_code == 0
    ms.current.assert_called_once()


def test_cli_db_history() -> None:
    """Verify db history command delegates to MigrationService."""
    cli = CLI()
    with patch.object(cli, "_get_migration_service") as mock_get_ms:
        ms = mock_get_ms.return_value
        exit_code = cli.execute(["db", "history"])
    assert exit_code == 0
    ms.history.assert_called_once()


def test_cli_db_revision() -> None:
    """Verify db revision command delegates to MigrationService."""
    cli = CLI()
    with patch.object(cli, "_get_migration_service") as mock_get_ms:
        ms = mock_get_ms.return_value
        exit_code = cli.execute(["db", "revision", "-m", "msg", "--autogenerate"])
    assert exit_code == 0
    ms.revision.assert_called_once_with(message="msg", autogenerate=True)


def test_cli_db_error() -> None:
    """Verify db command handles errors cleanly."""
    cli = CLI()
    with patch.object(cli, "_get_migration_service") as mock_get_ms:
        ms = mock_get_ms.return_value
        ms.upgrade.side_effect = Exception("db failed")
        with patch("builtins.print") as mock_print:
            exit_code = cli.execute(["db", "upgrade"])
    assert exit_code == 1
    mock_print.assert_any_call("[ERROR] Database command 'upgrade' failed: db failed")


def test_main_cli_execution() -> None:
    """Verify that the entry point main method executes CLI and exit."""
    with patch("app.cli.CLI") as mock_cli_class:
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.execute.return_value = 0

        with pytest.raises(SystemExit) as exc_info:
            main(["run"])

        assert exc_info.value.code == 0
        mock_cli_class.assert_called_once()
        mock_cli_instance.execute.assert_called_once_with(["run"])


def test_main_cli_execution_exception() -> None:
    """Verify that main method exits with 1 when execute throws an unhandled exception."""
    with patch("app.cli.CLI") as mock_cli_class:
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.execute.side_effect = RuntimeError("Fatal parsing crash")

        with pytest.raises(SystemExit) as exc_info:
            main(["run"])

        assert exc_info.value.code == 1
