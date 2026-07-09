"""User service for coordinating profile alterations and user administration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.database.user_repository import UserRepository
from app.database.session import get_session
from app.models.user import User, UserRole

if TYPE_CHECKING:
    from app.core.settings import Settings

__all__ = ["UserService"]


class UserService:
    """Service managing user profiles and system administration permissions."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the user service.

        Args:
            settings: Settings container.
        """
        self._settings = settings

    def profile(self, user_id: int) -> User:
        """Retrieve user details by ID.

        Args:
            user_id: User target database ID.

        Returns:
            The matched User model.

        Raises:
            ValueError: If user not found.
        """
        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found.")
            return user

    def update_profile(
        self, user_id: int, email: str | None = None, username: str | None = None
    ) -> User:
        """Modify profile attributes for a user.

        Args:
            user_id: User target database ID.
            email: New email value candidate.
            username: New username value candidate.

        Returns:
            The updated User model.

        Raises:
            ValueError: If user not found or conflict occurs.
        """
        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found.")

            if username and username != user.username:
                if user_repo.get_by_username(username):
                    raise ValueError("Username already taken.")
                user.username = username

            if email and email != user.email:
                if user_repo.get_by_email(email):
                    raise ValueError("Email already taken.")
                user.email = email

            user_repo.update(user)
            return user

    def deactivate_account(self, user_id: int) -> User:
        """Disable a user account.

        Args:
            user_id: User ID.

        Returns:
            The updated User model.
        """
        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found.")

            user.is_active = False
            user_repo.update(user)
            return user

    def activate_account(self, user_id: int) -> User:
        """Enable a deactivated user account.

        Args:
            user_id: User ID.

        Returns:
            The updated User model.
        """
        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found.")

            user.is_active = True
            user_repo.update(user)
            return user

    def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List platform users.

        Args:
            skip: Count offset skip.
            limit: Limit bounds size.

        Returns:
            List of users.
        """
        with get_session() as session:
            user_repo = UserRepository(session)
            return user_repo.list_users(skip=skip, limit=limit)

    def delete_user(self, user_id: int) -> None:
        """Permanently delete a user account.

        Args:
            user_id: Target user ID to destroy.
        """
        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(user_id)
            if user:
                user_repo.delete(user)

    def admin_update_user(
        self,
        user_id: int,
        username: str | None = None,
        email: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        is_verified: bool | None = None,
    ) -> User:
        """Allow admins to modify any user parameter.

        Args:
            user_id: Target user ID.
            username: New username candidate.
            email: New email candidate.
            role: New UserRole level.
            is_active: Active status toggle.
            is_verified: Email verification toggle.

        Returns:
            The updated User model.

        Raises:
            ValueError: If user not found or conflict occurs.
        """
        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found.")

            if username and username != user.username:
                if user_repo.get_by_username(username):
                    raise ValueError("Username already taken.")
                user.username = username

            if email and email != user.email:
                if user_repo.get_by_email(email):
                    raise ValueError("Email already taken.")
                user.email = email

            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active
            if is_verified is not None:
                user.is_verified = is_verified

            user_repo.update(user)
            return user
