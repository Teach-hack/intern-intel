"""Stateless dependency injection providers for REST API."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.database.session import get_session
from app.database.user_repository import UserRepository
from app.models.user import User, UserRole
from app.notifications.message_builder import MessageBuilder
from app.notifications.notification_service import NotificationService
from app.notifications.telegram import TelegramNotifier
from app.registry import create_default_registry
from app.security.tokens import verify_token
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
    "get_current_user",
    "get_current_active_user",
    "get_admin_user",
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


# =============================================================================
# Authentication & Authorization Dependencies
# =============================================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login",
    auto_error=True,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    """Extract and verify user identity claims from the active access JWT.

    Args:
        token: Extracted access token.
        session: Active database transaction.

    Returns:
        The authenticated User model representation.

    Raises:
        HTTPException: If token is expired or user does not exist.
    """
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(session)
    user = user_repo.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Verify that the authenticated user profile is active.

    Args:
        user: Active authenticated user.

    Returns:
        The matched user profile.

    Raises:
        HTTPException: If the account has been disabled.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return user


def get_admin_user(
    user: User = Depends(get_current_active_user),
) -> User:
    """Restrict access to users holding the ADMIN role level.

    Args:
        user: Active authenticated user.

    Returns:
        The verified administrator user.

    Raises:
        HTTPException: If the account lacks admin privileges.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required.",
        )
    return user
