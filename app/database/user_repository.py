"""Repository for performing CRUD operations on User entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

__all__ = ["UserRepository"]


class UserRepository:
    """Repository for performing CRUD operations on User entities.

    This repository is responsible only for database operations.
    Transaction management (commit/rollback) must be handled by the caller.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Active SQLAlchemy database session.
        """
        self._session = session

    def create(self, user: User) -> User:
        """Create a new user record.

        Args:
            user: User instance to persist.

        Returns:
            The persisted User instance.
        """
        # Normalize fields before persistence
        if user.username:
            user.username = user.username.strip()
        if user.email:
            user.email = user.email.lower().strip()

        self._session.add(user)
        self._session.flush()
        return user

    def update(self, user: User) -> User:
        """Update an existing user record.

        Args:
            user: User instance to update.

        Returns:
            The updated User instance.
        """
        # Normalize fields before update
        if user.username:
            user.username = user.username.strip()
        if user.email:
            user.email = user.email.lower().strip()

        self._session.add(user)
        self._session.flush()
        return user

    def delete(self, user: User) -> None:
        """Delete a user record.

        Args:
            user: User instance to remove.
        """
        self._session.delete(user)
        self._session.flush()

    def exists(self, username: str, email: str) -> bool:
        """Check whether a user with username or email already exists.

        Args:
            username: User account username.
            email: User account email.

        Returns:
            True if user exists, otherwise False.
        """
        stmt = (
            select(User.id)
            .where(
                (func.lower(User.username) == username.lower().strip())
                | (func.lower(User.email) == email.lower().strip())
            )
            .limit(1)
        )
        return self._session.scalar(stmt) is not None

    def get_by_id(self, id: int) -> User | None:
        """Retrieve a user by their ID.

        Args:
            id: User primary key ID.

        Returns:
            Matching User if found, otherwise None.
        """
        return self._session.get(User, id)

    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address.

        Args:
            email: User account email.

        Returns:
            Matching User if found, otherwise None.
        """
        stmt = (
            select(User).where(func.lower(User.email) == email.lower().strip()).limit(1)
        )
        return self._session.scalar(stmt)

    def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username.

        Args:
            username: User account username.

        Returns:
            Matching User if found, otherwise None.
        """
        stmt = (
            select(User)
            .where(func.lower(User.username) == username.lower().strip())
            .limit(1)
        )
        return self._session.scalar(stmt)

    def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List users with offset boundaries.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of User objects.
        """
        stmt = select(User).order_by(User.id).offset(skip).limit(limit)
        return list(self._session.scalars(stmt).all())
