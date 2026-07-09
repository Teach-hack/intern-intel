"""Decoupled login throttling interface and in-memory implementation."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

__all__ = ["LoginThrottleInterface", "InMemoryLoginThrottle"]


class LoginThrottleInterface:
    """Interface for checking and recording login attempts.

    Allows plugging in distributed backend storage (e.g. Redis) without altering
    the authentication service logic.
    """

    def is_locked(self, username: str) -> bool:
        """Check whether the username is currently locked out.

        Args:
            username: Target user username/email.

        Returns:
            True if locked, otherwise False.
        """
        raise NotImplementedError

    def get_remaining_lockout(self, username: str) -> int:
        """Get remaining lockout duration in seconds.

        Args:
            username: Target user username/email.

        Returns:
            Remaining seconds.
        """
        raise NotImplementedError

    def record_failure(self, username: str) -> None:
        """Record a failed login attempt.

        Args:
            username: Target user username/email.
        """
        raise NotImplementedError

    def reset(self, username: str) -> None:
        """Reset failed attempt counters for a username.

        Args:
            username: Target user username/email.
        """
        raise NotImplementedError


class InMemoryLoginThrottle(LoginThrottleInterface):
    """Thread-safe in-memory login throttling implementation."""

    def __init__(
        self, max_attempts: int = 5, lockout_duration_minutes: int = 15
    ) -> None:
        """Initialize the in-memory throttle.

        Args:
            max_attempts: Number of failures allowed before lockout.
            lockout_duration_minutes: Duration of lockout in minutes.
        """
        self._max_attempts = max_attempts
        self._lockout_duration = timedelta(minutes=lockout_duration_minutes)
        self._lock = threading.Lock()
        self._failed_attempts: dict[
            str, tuple[int, datetime]
        ] = {}  # username -> (count, lockout_expiry)

    def is_locked(self, username: str) -> bool:
        """Check whether the username is currently locked out."""
        key = username.lower().strip()
        now = datetime.now(timezone.utc)
        with self._lock:
            if key in self._failed_attempts:
                count, expiry = self._failed_attempts[key]
                if count >= self._max_attempts:
                    if now < expiry:
                        return True
                    # Expired lockout: clean up
                    self._failed_attempts.pop(key, None)
        return False

    def get_remaining_lockout(self, username: str) -> int:
        """Get remaining lockout duration in seconds."""
        key = username.lower().strip()
        now = datetime.now(timezone.utc)
        with self._lock:
            if key in self._failed_attempts:
                _, expiry = self._failed_attempts[key]
                if now < expiry:
                    return int((expiry - now).total_seconds())
        return 0

    def record_failure(self, username: str) -> None:
        """Record a failed login attempt."""
        key = username.lower().strip()
        now = datetime.now(timezone.utc)
        with self._lock:
            count, expiry = self._failed_attempts.get(key, (0, now))
            count += 1
            if count >= self._max_attempts:
                expiry = now + self._lockout_duration
            self._failed_attempts[key] = (count, expiry)

    def reset(self, username: str) -> None:
        """Reset failed attempt counters for a username."""
        key = username.lower().strip()
        with self._lock:
            self._failed_attempts.pop(key, None)
