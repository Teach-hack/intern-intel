"""Authentication service coordinating user registrations, logins, and session lifecycles."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from app.database.refresh_token_repository import RefreshTokenRepository
from app.database.user_repository import UserRepository
from app.database.session import get_session
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.security.pwd_context import hash_password, verify_password
from app.security.throttle import InMemoryLoginThrottle, LoginThrottleInterface
from app.security.tokens import create_access_token

if TYPE_CHECKING:
    from app.core.settings import Settings

__all__ = ["AuthenticationService"]

# Shared default throttle to maintain lockouts across requests
_default_throttle = InMemoryLoginThrottle()


def _hash_token(token: str) -> str:
    """Hash a token using SHA-256 for secure database storage.

    Args:
        token: Plain text token.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthenticationService:
    """Service managing credentials check, session creation, and lockouts."""

    def __init__(
        self, settings: Settings, throttle: LoginThrottleInterface | None = None
    ) -> None:
        """Initialize the authentication service.

        Args:
            settings: Strong settings instance.
            throttle: Pluggable lockout manager.
        """
        self._settings = settings
        self._throttle = throttle or _default_throttle

    def _check_lockout(self, username: str) -> None:
        """Verify whether a user account is locked out.

        Args:
            username: Target user identifier.

        Raises:
            ValueError: If the account is locked.
        """
        if self._throttle.is_locked(username):
            remaining = self._throttle.get_remaining_lockout(username)
            raise ValueError(
                f"Account is temporarily locked out due to multiple failed login attempts. "
                f"Please try again in {remaining} seconds."
            )

    def _record_failed_login(self, username: str) -> None:
        """Increment failed attempts and apply lockout if limit is reached.

        Args:
            username: Target user identifier.
        """
        self._throttle.record_failure(username)

    def _reset_failed_logins(self, username: str) -> None:
        """Reset failed login count for a user.

        Args:
            username: Target user identifier.
        """
        self._throttle.reset(username)

    def register(
        self, username: str, email: str, password: str, role: UserRole = UserRole.USER
    ) -> User:
        """Register a new user account with strict complexity checks.

        Args:
            username: Account username candidate.
            email: Account email candidate.
            password: Raw text password candidate.
            role: Privilege role assignment.

        Returns:
            The created User instance.

        Raises:
            ValueError: If requirements fail or duplicate exists.
        """
        clean_username = username.strip()
        clean_email = email.lower().strip()

        if not clean_username:
            raise ValueError("Username must not be empty.")
        if not clean_email:
            raise ValueError("Email must not be empty.")

        # Strict password checks
        if len(password) < self._settings.password_min_length:
            raise ValueError(
                f"Password must be at least {self._settings.password_min_length} characters long."
            )
        if len(password) > self._settings.password_max_length:
            raise ValueError(
                f"Password must not exceed {self._settings.password_max_length} characters long."
            )
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit.")

        with get_session() as session:
            user_repo = UserRepository(session)
            if user_repo.exists(clean_username, clean_email):
                raise ValueError("Username or Email already registered.")

            user = User(
                username=clean_username,
                email=clean_email,
                password_hash=hash_password(password),
                role=role,
                is_active=True,
                is_verified=False,
            )
            user_repo.create(user)
            return user

    def login(
        self, username_or_email: str, password: str, device_name: str | None = None
    ) -> dict[str, Any]:
        """Authenticate user credentials and issue active session tokens.

        Args:
            username_or_email: Credential identifier.
            password: Credential secret.
            device_name: Optional device label.

        Returns:
            Dictionary containing tokens.

        Raises:
            ValueError: If credentials fail or account is inactive.
        """
        self._check_lockout(username_or_email)

        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_username(
                username_or_email
            ) or user_repo.get_by_email(username_or_email)

            if not user or not verify_password(password, user.password_hash):
                self._record_failed_login(username_or_email)
                raise ValueError("Invalid username or password.")

            if not user.is_active:
                raise ValueError("User account is deactivated.")

            self._reset_failed_logins(username_or_email)

            # Generate token strings
            access_token = create_access_token(user.username)
            refresh_token = secrets.token_urlsafe(64)

            # Persist hashed refresh token
            token_repo = RefreshTokenRepository(session)
            expires = (
                datetime.now(timezone.utc)
                + timedelta(days=self._settings.refresh_token_expire_days)
            ).replace(tzinfo=None)
            token_model = RefreshToken(
                user_id=user.id,
                token_hash=_hash_token(refresh_token),
                expires_at=expires,
                device_name=device_name,
            )
            token_repo.create(token_model)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self._settings.access_token_expire_minutes * 60,
            }

    def refresh_session(
        self, refresh_token: str, device_name: str | None = None
    ) -> dict[str, Any]:
        """Perform token rotation and family check validation.

        Args:
            refresh_token: Plain text refresh token.
            device_name: Optional device label.

        Returns:
            Dictionary containing new tokens.

        Raises:
            ValueError: If validation fails or breach is detected.
        """
        hashed = _hash_token(refresh_token)

        with get_session() as session:
            token_repo = RefreshTokenRepository(session)
            user_repo = UserRepository(session)

            # Check if token exists in DB at all (whether revoked or not)
            from sqlalchemy import select

            stmt = (
                select(RefreshToken).where(RefreshToken.token_hash == hashed).limit(1)
            )
            token_record = session.scalar(stmt)

            if not token_record:
                raise ValueError("Invalid or expired refresh token.")

            # Reuse detection
            if (
                token_record.revoked_at is not None
                or token_record.expires_at
                <= datetime.now(timezone.utc).replace(tzinfo=None)
            ):
                # Potential token reuse breach! Revoke everything for this user.
                token_repo.revoke_all(token_record.user_id)
                raise ValueError(
                    "Refresh token has been revoked or expired. Security breach detected; all sessions revoked."
                )

            # Valid token found: rotate it
            user = user_repo.get_by_id(token_record.user_id)
            if not user or not user.is_active:
                raise ValueError("Invalid user status.")

            # Revoke current token
            token_repo.revoke(token_record)

            # Generate new tokens
            new_access_token = create_access_token(user.username)
            new_refresh_token = secrets.token_urlsafe(64)

            # Save new token
            expires = (
                datetime.now(timezone.utc)
                + timedelta(days=self._settings.refresh_token_expire_days)
            ).replace(tzinfo=None)
            new_token_model = RefreshToken(
                user_id=user.id,
                token_hash=_hash_token(new_refresh_token),
                expires_at=expires,
                device_name=device_name or token_record.device_name,
            )
            token_repo.create(new_token_model)

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": self._settings.access_token_expire_minutes * 60,
            }

    def logout(self, refresh_token: str) -> None:
        """Invalidate the session matching the target refresh token.

        Args:
            refresh_token: Target token to revoke.
        """
        hashed = _hash_token(refresh_token)
        with get_session() as session:
            token_repo = RefreshTokenRepository(session)
            from sqlalchemy import select

            stmt = (
                select(RefreshToken).where(RefreshToken.token_hash == hashed).limit(1)
            )
            token_record = session.scalar(stmt)
            if token_record and token_record.revoked_at is None:
                token_repo.revoke(token_record)

    def logout_all(self, user_id: int) -> None:
        """Revoke all login sessions for a user.

        Args:
            user_id: Target user identifier.
        """
        with get_session() as session:
            token_repo = RefreshTokenRepository(session)
            token_repo.revoke_all(user_id)

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> None:
        """Modify user credentials with strict password length constraints.

        Args:
            user_id: Target user ID.
            old_password: Confirm current password.
            new_password: New password replacement.

        Raises:
            ValueError: If requirements fail.
        """
        if len(new_password) < self._settings.password_min_length:
            raise ValueError(
                f"Password must be at least {self._settings.password_min_length} characters long."
            )
        if len(new_password) > self._settings.password_max_length:
            raise ValueError(
                f"Password must not exceed {self._settings.password_max_length} characters long."
            )

        with get_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found.")

            if not verify_password(old_password, user.password_hash):
                raise ValueError("Invalid current password.")

            user.password_hash = hash_password(new_password)
            user_repo.update(user)

            # Revoke all sessions on credential change for safety
            token_repo = RefreshTokenRepository(session)
            token_repo.revoke_all(user_id)

    # =========================================================================
    # SaaS / SaaS Extensions Roadmap Placeholders
    # =========================================================================

    def verify_email(self, user_id: int, code: str) -> bool:
        """Verify user email address using verification code.

        Extension hook for future email verification flows.
        """
        # FUTURE: Query verification token table and mark user as verified
        return True

    def initiate_password_reset(self, email: str) -> str:
        """Generate reset token and dispatch password reset instructions.

        Extension hook for future self-serve password resets.
        """
        # FUTURE: Generate secure token, store in cache/DB, dispatch email template
        return "placeholder-reset-token"

    def oauth_login_callback(self, provider: str, oauth_code: str) -> dict[str, Any]:
        """Authenticate user via Google or GitHub OAuth.

        Extension hook for future third-party OAuth provider integrations.
        """
        # FUTURE: Exchange code with provider API, check or create User, return login tokens
        return {"provider": provider, "status": "oauth-placeholder"}

    def authenticate_api_key(self, api_key: str) -> User | None:
        """Verify API key and retrieve corresponding User profile.

        Extension hook for developer access tokens/keys integrations.
        """
        # FUTURE: Query API Keys table and return linked active user
        return None

    def verify_mfa_code(self, user_id: int, mfa_code: str) -> bool:
        """Verify multi-factor authentication code.

        Extension hook for future MFA/2FA validation flows.
        """
        # FUTURE: Validate TOTP token using PyOTP or equivalent library
        return True

    def create_organization_team(self, user_id: int, name: str) -> dict[str, Any]:
        """Create a new multi-tenant organization or team.

        Extension hook for future B2B SaaS team collaboration capabilities.
        """
        # FUTURE: Persist organization record and link user as owner/admin
        return {"org_name": name, "owner_id": user_id, "status": "placeholder"}
