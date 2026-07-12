"""JWT token signing and claim verification utility."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_token",
]


def create_access_token(
    user: Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived access JWT token.

    Args:
        user: The authenticated User object.
        expires_delta: Optional override token expiration length.

    Returns:
        Encoded JWT token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user.username),
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a long-lived refresh JWT token.

    Args:
        subject: The subject identification (e.g. username).
        expires_delta: Optional override token expiration length.

    Returns:
        Encoded JWT token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "refresh",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str) -> dict[str, Any] | None:
    """Decode and verify claims of a signature-valid JWT.

    Args:
        token: Target JWT token.

    Returns:
        Decoded payload dict if valid, otherwise None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
        return payload
    except jwt.PyJWTError:
        return None
