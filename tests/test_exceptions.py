"""Unit tests for centralized application exceptions."""

from __future__ import annotations

import pytest

from app.core.exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseTransactionError,
    HttpClientError,
    HttpConnectionError,
    HttpRetryExhaustedError,
    HttpStatusError,
    HttpTimeoutError,
    InternIntelError,
    NotificationError,
    ScraperBlockedError,
    ScraperError,
    ScraperParsingError,
    TelegramNotificationError,
)


def test_exception_hierarchy() -> None:
    """Verify that exceptions follow the expected inheritance structure."""
    # Base application exception
    assert issubclass(InternIntelError, Exception)

    # Core/Configuration
    assert issubclass(ConfigurationError, InternIntelError)

    # HTTP Client
    assert issubclass(HttpClientError, InternIntelError)
    assert issubclass(HttpTimeoutError, HttpClientError)
    assert issubclass(HttpConnectionError, HttpClientError)
    assert issubclass(HttpStatusError, HttpClientError)
    assert issubclass(HttpRetryExhaustedError, HttpClientError)

    # Database
    assert issubclass(DatabaseError, InternIntelError)
    assert issubclass(DatabaseConnectionError, DatabaseError)
    assert issubclass(DatabaseTransactionError, DatabaseError)

    # Scrapers
    assert issubclass(ScraperError, InternIntelError)
    assert issubclass(ScraperParsingError, ScraperError)
    assert issubclass(ScraperBlockedError, ScraperError)

    # Notifications
    assert issubclass(NotificationError, InternIntelError)
    assert issubclass(TelegramNotificationError, NotificationError)


def test_base_exception_message() -> None:
    """Verify that InternIntelError preserves the error message via built-in behavior."""
    message = "An application error occurred"
    exc = InternIntelError(message)
    assert str(exc) == message


def test_http_status_error_attributes() -> None:
    """Verify that HttpStatusError preserves HTTP-specific attributes."""
    message = "Request failed with status code 404"
    status_code = 404
    url = "https://example.com/jobs"
    method = "GET"
    retry_count = 3

    # With attributes provided
    exc = HttpStatusError(
        message,
        status_code=status_code,
        url=url,
        method=method,
        retry_count=retry_count,
    )
    assert str(exc) == message
    assert exc.status_code == status_code
    assert exc.url == url
    assert exc.method == method
    assert exc.retry_count == retry_count

    # Default values
    exc_default = HttpStatusError(message)
    assert exc_default.status_code is None
    assert exc_default.url is None
    assert exc_default.method is None
    assert exc_default.retry_count is None


@pytest.mark.parametrize(
    "exc_class",
    [
        ConfigurationError,
        HttpClientError,
        HttpTimeoutError,
        HttpConnectionError,
        HttpRetryExhaustedError,
        DatabaseError,
        DatabaseConnectionError,
        DatabaseTransactionError,
        ScraperError,
        ScraperParsingError,
        ScraperBlockedError,
        NotificationError,
        TelegramNotificationError,
    ],
)
def test_other_exceptions_messages(exc_class: type[InternIntelError]) -> None:
    """Verify that other exceptions preserve their error messages."""
    message = f"Test error message for {exc_class.__name__}"
    exc = exc_class(message)
    assert str(exc) == message


def test_pytest_raises_behavior() -> None:
    """Verify that exceptions can be caught correctly using pytest.raises."""
    # Test catching root exception
    with pytest.raises(InternIntelError) as exc_info:
        raise ConfigurationError("Invalid key")
    assert str(exc_info.value) == "Invalid key"

    # Test catching specific HttpTimeoutError
    with pytest.raises(HttpTimeoutError) as exc_info:
        raise HttpTimeoutError("Request timed out")
    assert str(exc_info.value) == "Request timed out"

    # Test catching specific DatabaseConnectionError
    with pytest.raises(DatabaseConnectionError) as exc_info:
        raise DatabaseConnectionError("Failed to connect")
    assert str(exc_info.value) == "Failed to connect"

    # Test catching specific TelegramNotificationError
    with pytest.raises(TelegramNotificationError) as exc_info:
        raise TelegramNotificationError("Telegram send failure")
    assert str(exc_info.value) == "Telegram send failure"
