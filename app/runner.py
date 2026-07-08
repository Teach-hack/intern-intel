"""Runner for orchestrating the scraping and notification pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import settings as settings  # noqa: F401  # accessed via globals()
from app.core.logger import logger
from app.notifications.message_builder import MessageBuilder
from app.notifications.notification_service import NotificationService
from app.notifications.telegram import TelegramNotifier
from app.services.pipeline_service import PipelineService

if TYPE_CHECKING:
    from app.core.settings import Settings
    from app.models.internship import Internship

__all__ = ["Runner"]


class Runner:
    """Orchestrates scraping runs and subsequent notification dispatches."""

    def __init__(
        self,
        pipeline_service: PipelineService | None = None,
        notification_service: NotificationService | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize Runner with its services.

        Args:
            pipeline_service: Pipeline orchestrator instance.
            notification_service: Notification service instance.
            settings: Optional custom Settings container.
        """
        from app.registry import create_default_registry

        self._custom_settings = settings
        active_settings = self._active_settings

        self._pipeline_service = pipeline_service or PipelineService(
            registry=create_default_registry(settings=active_settings)
        )

        if notification_service is not None:
            self._notification_service = notification_service
        else:
            enabled = active_settings.get("notification.telegram", False)
            if isinstance(enabled, str):
                enabled = enabled.lower() in ("true", "1", "yes")
            else:
                enabled = bool(enabled)

            bot_token = active_settings.get("notification.telegram_bot_token")
            chat_id = active_settings.get("notification.telegram_chat_id")

            notifier = None
            if enabled and bot_token and chat_id:
                notifier = TelegramNotifier(
                    bot_token=str(bot_token),
                    chat_id=str(chat_id),
                )
            else:
                logger.info(
                    "Telegram notifications are disabled or incomplete in config."
                )

            self._notification_service = NotificationService(
                message_builder=MessageBuilder(),
                notifier=notifier,
            )

    @property
    def _active_settings(self) -> Settings:
        """Resolve current active settings instance dynamically."""
        if self._custom_settings is not None:
            return self._custom_settings
        return globals()["settings"]

    def run(self) -> list[Internship]:
        """Execute the scraper pipeline and send notifications for new listings.

        Returns:
            A list of new/saved Internship ORM model instances.
        """
        logger.info("Application started.")

        try:
            saved_jobs = self._pipeline_service.run()
            logger.info("Pipeline completed.")

            if saved_jobs:
                if self._notification_service._notifier is not None:
                    logger.info("New internships found: {}", len(saved_jobs))
                    self._notification_service.notify_many(saved_jobs)
                    logger.info("Notifications sent.")
                else:
                    logger.info(
                        "Notifications skipped (notifier not configured/enabled)."
                    )
            else:
                logger.info("No internships found.")

            logger.info("Application finished.")
            return saved_jobs

        except Exception as exc:
            logger.exception("Application runner execution failed: {}", exc)
            raise
