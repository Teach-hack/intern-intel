"""Repository for performing database operations on RefreshToken entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import delete, select, update

from app.models.refresh_token import RefreshToken

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

__all__ = ["RefreshTokenRepository"]


class RefreshTokenRepository:
    """Repository for performing CRUD operations on RefreshToken entities.

    This repository is responsible only for database operations.
    Transaction management (commit/rollback) must be handled by the caller.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Active SQLAlchemy database session.
        """
        self._session = session

    def create(self, token: RefreshToken) -> RefreshToken:
        """Create a new refresh token record.

        Args:
            token: RefreshToken instance to persist.

        Returns:
            The persisted RefreshToken instance.
        """
        self._session.add(token)
        self._session.flush()
        return token

    def revoke(self, token: RefreshToken) -> None:
        """Revoke a refresh token by setting its revoked_at field.

        Args:
            token: Target RefreshToken instance.
        """
        token.revoked_at = datetime.now(timezone.utc)
        self._session.add(token)
        self._session.flush()

    def revoke_all(self, user_id: int) -> None:
        """Revoke all active refresh tokens for a user.

        Args:
            user_id: ID of the user.
        """
        stmt = (
            update(RefreshToken)
            .where(
                (RefreshToken.user_id == user_id) & (RefreshToken.revoked_at.is_(None))
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        self._session.execute(stmt)
        self._session.flush()

    def get_valid_token(self, token_hash: str) -> RefreshToken | None:
        """Retrieve a valid (non-expired, non-revoked) refresh token by its hash.

        Args:
            token_hash: Hashed refresh token value.

        Returns:
            RefreshToken if valid, otherwise None.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = (
            select(RefreshToken)
            .where(
                (RefreshToken.token_hash == token_hash)
                & (RefreshToken.revoked_at.is_(None))
                & (RefreshToken.expires_at > now)
            )
            .limit(1)
        )
        return self._session.scalar(stmt)

    def delete_expired(self) -> int:
        """Delete all expired or revoked refresh tokens.

        Returns:
            Number of deleted token rows.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = delete(RefreshToken).where(
            (RefreshToken.expires_at <= now) | (RefreshToken.revoked_at.is_not(None))
        )
        res = self._session.execute(stmt)
        self._session.flush()
        count = res.rowcount  # type: ignore[attr-defined]
        return int(count) if count is not None else 0
