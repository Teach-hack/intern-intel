"""Unit tests for the Runner class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ScraperError
from app.models.internship import Internship
from app.notifications.notification_service import NotificationService
from app.notifications.telegram import TelegramNotifier
from app.runner import Runner
from app.services.pipeline_service import PipelineService


@pytest.fixture
def mock_pipeline_service() -> MagicMock:
    """Fixture to provide a mocked PipelineService."""
    return MagicMock(spec=PipelineService)


@pytest.fixture
def mock_notification_service() -> MagicMock:
    """Fixture to provide a mocked NotificationService."""
    mock = MagicMock(spec=NotificationService)
    # Give it a mocked _notifier attribute for tracking if it's configured
    mock._notifier = MagicMock()
    return mock


def test_runner_initialization_defaults() -> None:
    """Verify default instantiation of PipelineService and NotificationService."""
    # We patch settings to avoid reading files or trying to configure actual objects
    with patch("app.runner.settings") as mock_settings:
        mock_settings.get.return_value = False
        runner = Runner()
        assert isinstance(runner._pipeline_service, PipelineService)
        assert isinstance(runner._notification_service, NotificationService)


def test_runner_dependency_injection(
    mock_pipeline_service: MagicMock,
    mock_notification_service: MagicMock,
) -> None:
    """Verify correct injection of pipeline and notification services."""
    runner = Runner(
        pipeline_service=mock_pipeline_service,
        notification_service=mock_notification_service,
    )
    assert runner._pipeline_service is mock_pipeline_service
    assert runner._notification_service is mock_notification_service


def test_runner_run_successful_with_jobs(
    mock_pipeline_service: MagicMock,
    mock_notification_service: MagicMock,
) -> None:
    """Verify run pipeline succeeds and sends notifications when jobs are found."""
    jobs = [
        Internship(
            company="Google",
            title="SWE Intern",
            url="https://google.com/1",
            employment_type="internship",
            work_mode="remote",
            source="google",
            status="new",
        )
    ]
    mock_pipeline_service.run.return_value = jobs

    runner = Runner(
        pipeline_service=mock_pipeline_service,
        notification_service=mock_notification_service,
    )

    with patch("app.runner.logger") as mock_logger:
        result = runner.run()

    assert result == jobs
    mock_pipeline_service.run.assert_called_once()
    mock_notification_service.notify_many.assert_called_once_with(jobs)

    # Verify expected logs
    mock_logger.info.assert_any_call("Application started.")
    mock_logger.info.assert_any_call("Pipeline completed.")
    mock_logger.info.assert_any_call("New internships found: {}", len(jobs))
    mock_logger.info.assert_any_call("Notifications sent.")
    mock_logger.info.assert_any_call("Application finished.")


def test_runner_run_no_jobs(
    mock_pipeline_service: MagicMock,
    mock_notification_service: MagicMock,
) -> None:
    """Verify run pipeline completes but skips notifications when no jobs are found."""
    mock_pipeline_service.run.return_value = []

    runner = Runner(
        pipeline_service=mock_pipeline_service,
        notification_service=mock_notification_service,
    )

    with patch("app.runner.logger") as mock_logger:
        result = runner.run()

    assert result == []
    mock_pipeline_service.run.assert_called_once()
    mock_notification_service.notify_many.assert_not_called()

    # Verify expected logs
    mock_logger.info.assert_any_call("Application started.")
    mock_logger.info.assert_any_call("Pipeline completed.")
    mock_logger.info.assert_any_call("No internships found.")
    mock_logger.info.assert_any_call("Application finished.")


def test_runner_run_notification_skipped_not_configured(
    mock_pipeline_service: MagicMock,
) -> None:
    """Verify run skips notifying and logs skip when notifier is not set."""
    jobs = [
        Internship(
            company="Google",
            title="SWE Intern",
            url="https://google.com/1",
            employment_type="internship",
            work_mode="remote",
            source="google",
            status="new",
        )
    ]
    mock_pipeline_service.run.return_value = jobs

    # NotificationService with no notifier
    mock_notification_service = NotificationService(notifier=None)

    runner = Runner(
        pipeline_service=mock_pipeline_service,
        notification_service=mock_notification_service,
    )

    with patch("app.runner.logger") as mock_logger:
        result = runner.run()

    assert result == jobs
    mock_pipeline_service.run.assert_called_once()

    # Verify expected logs
    mock_logger.info.assert_any_call("Application started.")
    mock_logger.info.assert_any_call("Pipeline completed.")
    mock_logger.info.assert_any_call(
        "Notifications skipped (notifier not configured/enabled)."
    )
    mock_logger.info.assert_any_call("Application finished.")


def test_runner_run_exception_propagation(
    mock_pipeline_service: MagicMock,
    mock_notification_service: MagicMock,
) -> None:
    """Verify exceptions raised by pipeline propagate and are logged."""
    mock_pipeline_service.run.side_effect = ScraperError("Pipeline crashed")

    runner = Runner(
        pipeline_service=mock_pipeline_service,
        notification_service=mock_notification_service,
    )

    with patch("app.runner.logger") as mock_logger:
        with pytest.raises(ScraperError, match="Pipeline crashed"):
            runner.run()

    mock_logger.info.assert_any_call("Application started.")
    mock_logger.exception.assert_called_once()


def test_runner_initialization_with_configured_notifier() -> None:
    """Verify initialization constructs TelegramNotifier when enabled and configured in settings."""
    with patch("app.runner.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: {
            "notification.telegram": True,
            "notification.telegram_bot_token": "test-token",
            "notification.telegram_chat_id": "test-chat-id",
        }.get(key, default)

        runner = Runner()
        assert runner._notification_service is not None
        assert isinstance(runner._notification_service._notifier, TelegramNotifier)
        assert runner._notification_service._notifier._bot_token == "test-token"
        assert runner._notification_service._notifier._chat_id == "test-chat-id"
