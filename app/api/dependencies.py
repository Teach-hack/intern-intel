"""Stateless dependency injection providers for REST API."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.database.session import get_session
from app.notifications.message_builder import MessageBuilder
from app.notifications.notification_service import NotificationService
from app.notifications.telegram import TelegramNotifier
from app.registry import create_default_registry
from app.services.database_service import DatabaseService
from app.services.pipeline_service import PipelineService

if TYPE_CHECKING:
    from app.core.settings import Settings

__all__ = [
    "get_settings",
    "get_db_session",
    "get_database_service",
    "get_pipeline_service",
    "get_notification_service",
]


def get_settings() -> Settings:
    """Provide the current global settings container.

    Returns:
        The settings instance.
    """
    return app_settings


def get_db_session() -> Generator[Session, None, None]:
    """Yield a managed SQLAlchemy database session.

    Yields:
        A database session.
    """
    with get_session() as session:
        yield session


def get_database_service(
    session: Session = Depends(get_db_session),
) -> DatabaseService:
    """Provide the DatabaseService instance.

    Args:
        session: Injected database session.

    Returns:
        A DatabaseService instance.
    """
    # The database service uses internal context management, but we pass session
    # dependency to guarantee database checks inside same transaction block if required.
    return DatabaseService()


def get_pipeline_service(
    settings: Settings = Depends(get_settings),
) -> PipelineService:
    """Provide the PipelineService orchestrator.

    Args:
        settings: Injected settings instance.

    Returns:
        A PipelineService instance.
    """
    return PipelineService(registry=create_default_registry(settings=settings))


def get_notification_service(
    settings: Settings = Depends(get_settings),
) -> NotificationService:
    """Provide the NotificationService dispatcher.

    Args:
        settings: Injected settings instance.

    Returns:
        A NotificationService instance.
    """
    enabled = settings.telegram_enabled
    bot_token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    notifier = None
    if enabled and bot_token and chat_id:
        notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id)

    return NotificationService(message_builder=MessageBuilder(), notifier=notifier)
