"""Notification service layer for dispatching internship messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logger import logger
from app.notifications.message_builder import MessageBuilder
from app.notifications.telegram import TelegramNotifier

if TYPE_CHECKING:
    from app.models.internship import Internship

__all__ = ["NotificationService"]


class NotificationService:
    """Service coordinates building and sending internship notifications."""

    def __init__(
        self,
        message_builder: MessageBuilder | None = None,
        notifier: TelegramNotifier | None = None,
    ) -> None:
        """Initialize the NotificationService.

        Args:
            message_builder: Instance of MessageBuilder for formatting.
            notifier: Instance of TelegramNotifier to deliver messages.
        """
        self._message_builder = message_builder or MessageBuilder()
        self._notifier = notifier

    def notify(self, job: Internship) -> None:
        """Send a notification for a single internship listing.

        Args:
            job: The internship listing database model instance.
        """
        if not self._notifier:
            logger.warning(
                "Telegram notifier is not configured. Skipping notification."
            )
            return

        logger.info("Building notification message for internship: {}", job.title)
        message = self._message_builder.build(job)

        logger.info("Sending notification message to Telegram.")
        self._notifier.send(message)
        logger.info("Notification sent successfully.")

    def notify_many(self, jobs: list[Internship]) -> None:
        """Send a combined notification for multiple internship listings.

        Args:
            jobs: A list of internship listings.
        """
        if not jobs:
            logger.info("No internships to notify. Returning immediately.")
            return

        if not self._notifier:
            logger.warning(
                "Telegram notifier is not configured. Skipping notification."
            )
            return

        logger.info("Building notification message for {} internships.", len(jobs))
        message = self._message_builder.build_many(jobs)

        logger.info("Sending bulk notification message to Telegram.")
        self._notifier.send(message)
        logger.info("Bulk notification sent successfully.")
