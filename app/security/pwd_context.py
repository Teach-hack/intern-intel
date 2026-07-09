"""Password hashing context utilizing bcrypt directly."""

from __future__ import annotations

import bcrypt

__all__ = ["hash_password", "verify_password"]


def hash_password(password: str) -> str:
    """Hash a raw text password using bcrypt directly.

    Args:
        password: Raw password string.

    Returns:
        The hashed password representation.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a stored bcrypt hash.

    Args:
        plain_password: Plain text password candidate.
        hashed_password: Hashed password database representation.

    Returns:
        True if the password matches, otherwise False.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False
