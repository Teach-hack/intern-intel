"""Basic in-memory rate limiter for authentication endpoints."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException, Request, status

# In-memory store: { ip_address: RateLimitData }
_RATE_LIMIT_STORE: dict[str, "RateLimitData"] = defaultdict(lambda: RateLimitData())


@dataclass
class RateLimitData:
    """Store for tracking failed attempts and lockouts."""

    failures: int = 0
    locked_until: float = 0.0


def rate_limit(max_failures: int = 5, lock_duration_seconds: int = 900) -> Callable:
    """Dependency generator to rate limit specific IP addresses.

    Args:
        max_failures: Max allowed failures before lockout.
        lock_duration_seconds: Lockout duration in seconds.

    Returns:
        FastAPI dependency function.
    """

    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        data = _RATE_LIMIT_STORE[client_ip]

        now = time.time()

        if data.locked_until > now:
            remaining = int((data.locked_until - now) / 60) or 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Try again in {remaining} minutes.",
            )

    return dependency


def record_failed_attempt(
    ip_address: str, max_failures: int = 5, lock_duration_seconds: int = 900
) -> None:
    """Increment failure counter and potentially lock IP.

    Args:
        ip_address: Client IP address.
        max_failures: Threshold to trigger lock.
        lock_duration_seconds: Duration to lock.
    """
    data = _RATE_LIMIT_STORE[ip_address]
    data.failures += 1

    if data.failures >= max_failures:
        data.locked_until = time.time() + lock_duration_seconds
        data.failures = 0


def clear_failed_attempts(ip_address: str) -> None:
    """Reset the failure counter for an IP address.

    Args:
        ip_address: Client IP address.
    """
    if ip_address in _RATE_LIMIT_STORE:
        _RATE_LIMIT_STORE[ip_address].failures = 0
        _RATE_LIMIT_STORE[ip_address].locked_until = 0.0
