"""Unit tests for the NotificationService class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import TelegramNotificationError
from app.models.internship import Internship
from app.notifications.message_builder import MessageBuilder
from app.notifications.notification_service import NotificationService
from app.notifications.telegram import TelegramNotifier


@pytest.fixture
def mock_message_builder() -> MagicMock:
    """Fixture to provide a mocked MessageBuilder."""
    return MagicMock(spec=MessageBuilder)


@pytest.fixture
def mock_telegram_notifier() -> MagicMock:
    """Fixture to provide a mocked TelegramNotifier."""
    return MagicMock(spec=TelegramNotifier)


def test_initialization_defaults() -> None:
    """Verify that NotificationService initializes correct defaults."""
    service = NotificationService()
    assert isinstance(service._message_builder, MessageBuilder)
    assert service._notifier is None


def test_initialization_dependency_injection(
    mock_message_builder: MagicMock,
    mock_telegram_notifier: MagicMock,
) -> None:
    """Verify that dependencies are correctly injected."""
    service = NotificationService(
        message_builder=mock_message_builder,
        notifier=mock_telegram_notifier,
    )
    assert service._message_builder is mock_message_builder
    assert service._notifier is mock_telegram_notifier


def test_notify_notifier_not_configured(
    mock_message_builder: MagicMock,
) -> None:
    """Verify notify skips send when notifier is not set."""
    job = Internship(
        company="Google",
        title="Intern",
        url="https://google.com",
        employment_type="internship",
        work_mode="remote",
        source="google",
        status="new",
    )
    service = NotificationService(message_builder=mock_message_builder, notifier=None)

    with patch("app.notifications.notification_service.logger") as mock_logger:
        service.notify(job)

    mock_logger.warning.assert_called_once_with(
        "Telegram notifier is not configured. Skipping notification."
    )
    mock_message_builder.build.assert_not_called()


def test_notify_success(
    mock_message_builder: MagicMock,
    mock_telegram_notifier: MagicMock,
) -> None:
    """Verify successful notify formatting and sending."""
    job = Internship(
        company="Google",
        title="Intern",
        url="https://google.com",
        employment_type="internship",
        work_mode="remote",
        source="google",
        status="new",
    )
    mock_message_builder.build.return_value = "Formatted Job"

    service = NotificationService(
        message_builder=mock_message_builder,
        notifier=mock_telegram_notifier,
    )

    with patch("app.notifications.notification_service.logger") as mock_logger:
        service.notify(job)

    mock_message_builder.build.assert_called_once_with(job)
    mock_telegram_notifier.send.assert_called_once_with("Formatted Job")
    mock_logger.info.assert_any_call(
        "Building notification message for internship: {}", job.title
    )
    mock_logger.info.assert_any_call("Notification sent successfully.")


def test_notify_many_empty(
    mock_message_builder: MagicMock,
    mock_telegram_notifier: MagicMock,
) -> None:
    """Verify notify_many returns early when list is empty."""
    service = NotificationService(
        message_builder=mock_message_builder,
        notifier=mock_telegram_notifier,
    )

    with patch("app.notifications.notification_service.logger") as mock_logger:
        service.notify_many([])

    mock_message_builder.build_many.assert_not_called()
    mock_telegram_notifier.send.assert_not_called()
    mock_logger.info.assert_called_once_with(
        "No internships to notify. Returning immediately."
    )


def test_notify_many_notifier_not_configured(
    mock_message_builder: MagicMock,
) -> None:
    """Verify notify_many skips send when notifier is not set."""
    job = Internship(
        company="Google",
        title="Intern",
        url="https://google.com",
        employment_type="internship",
        work_mode="remote",
        source="google",
        status="new",
    )
    service = NotificationService(message_builder=mock_message_builder, notifier=None)

    with patch("app.notifications.notification_service.logger") as mock_logger:
        service.notify_many([job])

    mock_logger.warning.assert_called_once_with(
        "Telegram notifier is not configured. Skipping notification."
    )
    mock_message_builder.build_many.assert_not_called()


def test_notify_many_success(
    mock_message_builder: MagicMock,
    mock_telegram_notifier: MagicMock,
) -> None:
    """Verify successful notify_many formatting and sending."""
    job = Internship(
        company="Google",
        title="Intern",
        url="https://google.com",
        employment_type="internship",
        work_mode="remote",
        source="google",
        status="new",
    )
    mock_message_builder.build_many.return_value = "Formatted Jobs"

    service = NotificationService(
        message_builder=mock_message_builder,
        notifier=mock_telegram_notifier,
    )

    with patch("app.notifications.notification_service.logger") as mock_logger:
        service.notify_many([job])

    mock_message_builder.build_many.assert_called_once_with([job])
    mock_telegram_notifier.send.assert_called_once_with("Formatted Jobs")
    mock_logger.info.assert_any_call(
        "Building notification message for {} internships.", 1
    )
    mock_logger.info.assert_any_call("Bulk notification sent successfully.")


def test_notify_exception_propagation(
    mock_message_builder: MagicMock,
    mock_telegram_notifier: MagicMock,
) -> None:
    """Verify that exceptions from the notifier propagate through the service."""
    job = Internship(
        company="Google",
        title="Intern",
        url="https://google.com",
        employment_type="internship",
        work_mode="remote",
        source="google",
        status="new",
    )
    mock_message_builder.build.return_value = "Formatted Job"
    mock_telegram_notifier.send.side_effect = TelegramNotificationError("Send failure")

    service = NotificationService(
        message_builder=mock_message_builder,
        notifier=mock_telegram_notifier,
    )

    with pytest.raises(TelegramNotificationError, match="Send failure"):
        service.notify(job)
