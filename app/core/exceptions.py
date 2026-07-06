"""Centralized exception classes for the InternIntel application.

All application-specific exceptions inherit from the base class
:class:`InternIntelError`.
"""

from __future__ import annotations

__all__ = [
    "InternIntelError",
    "ConfigurationError",
    "HttpClientError",
    "HttpTimeoutError",
    "HttpConnectionError",
    "HttpStatusError",
    "HttpRetryExhaustedError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseTransactionError",
    "ScraperError",
    "ScraperParsingError",
    "ScraperBlockedError",
    "NotificationError",
    "TelegramNotificationError",
]


class InternIntelError(Exception):
    """Base exception for all InternIntel application errors."""


class ConfigurationError(InternIntelError):
    """Raised when configuration values are missing, invalid, or malformed."""


class HttpClientError(InternIntelError):
    """Base exception for all HTTP client and request failures."""


class HttpTimeoutError(HttpClientError):
    """Raised when an HTTP request times out."""


class HttpConnectionError(HttpClientError):
    """Raised when a network connection to the remote host cannot be established."""


class HttpStatusError(HttpClientError):
    """Raised when a request completes with an unsuccessful HTTP status code."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        url: str | None = None,
        method: str | None = None,
        retry_count: int | None = None,
    ) -> None:
        """Initialize the HTTP status error.

        Args:
            message: A human-readable error description.
            status_code: The HTTP status code received.
            url: The URL that was requested.
            method: The HTTP method used (e.g. GET, POST).
            retry_count: The number of retry attempts made before failing.
        """
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.method = method
        self.retry_count = retry_count


class HttpRetryExhaustedError(HttpClientError):
    """Raised when a request fails repeatedly and all retries are exhausted."""


class DatabaseError(InternIntelError):
    """Base exception for all database-related errors."""


class DatabaseConnectionError(DatabaseError):
    """Raised when connection to the database fails."""


class DatabaseTransactionError(DatabaseError):
    """Raised when a database transaction fails to commit or rollback."""


class ScraperError(InternIntelError):
    """Base exception for all scraper and scraper service failures."""


class ScraperParsingError(ScraperError):
    """Raised when a scraper fails to parse or normalize listing content."""


class ScraperBlockedError(ScraperError):
    """Raised when the crawler is blocked by rate limits or anti-bot systems."""


class NotificationError(InternIntelError):
    """Base exception for all notification dispatch failures."""


class TelegramNotificationError(NotificationError):
    """Raised when sending a notification to Telegram fails."""
