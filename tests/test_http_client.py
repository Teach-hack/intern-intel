"""Unit tests for the centralized HttpClient class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpTimeoutError,
)
from app.core.http_client import HttpClient, http_client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(
    mock_httpx: MagicMock | None = None,
    **config_overrides: object,
) -> HttpClient:
    """Build an ``HttpClient`` with mocked settings and optional httpx mock.

    Args:
        mock_httpx: Pre-configured ``httpx.Client`` mock.
        **config_overrides: Settings keys to override.
    """
    defaults: dict[str, object] = {
        "scraper.timeout": 30,
        "scraper.user_agent": "TestBot/1.0",
        "http.follow_redirects": True,
    }
    defaults.update(config_overrides)

    with patch("app.core.http_client.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: defaults.get(
            key, default
        )
        if mock_httpx is None:
            mock_httpx = MagicMock(spec=httpx.Client)
        return HttpClient(client=mock_httpx)


def _mock_response(status_code: int = 200) -> MagicMock:
    """Return a minimal ``httpx.Response`` mock."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    return resp


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_default_initialization() -> None:
    """Verify that HttpClient defaults to instantiating an httpx.Client."""
    with patch("app.core.http_client.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: default
        client = HttpClient()
    assert isinstance(client._client, httpx.Client)
    client.close()


def test_dependency_injection() -> None:
    """Verify that a pre-configured httpx.Client can be injected."""
    mock_httpx = MagicMock(spec=httpx.Client)
    client = _make_client(mock_httpx)
    assert client._client is mock_httpx


# ---------------------------------------------------------------------------
# GET requests
# ---------------------------------------------------------------------------


def test_get_request() -> None:
    """Verify that GET requests delegate to the underlying client."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    res = client.get("https://example.com/api", params={"q": "search"})

    assert res.status_code == 200
    mock_httpx.request.assert_called_once()
    call_args = mock_httpx.request.call_args
    assert call_args[0] == ("GET", "https://example.com/api")


def test_get_request_no_kwargs() -> None:
    """Verify that GET requests work without optional arguments."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    res = client.get("https://example.com/api")

    assert res.status_code == 200
    mock_httpx.request.assert_called_once()


# ---------------------------------------------------------------------------
# POST requests
# ---------------------------------------------------------------------------


def test_post_request() -> None:
    """Verify that POST requests delegate to the underlying client."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    res = client.post("https://example.com/api", json={"key": "value"})

    assert res.status_code == 200
    call_args = mock_httpx.request.call_args
    assert call_args[0] == ("POST", "https://example.com/api")


def test_post_with_json_body() -> None:
    """POST with a JSON body delegates correctly."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    client.post("https://example.com/api", json={"key": "value"})

    call_kwargs = mock_httpx.request.call_args[1]
    assert call_kwargs["json"] == {"key": "value"}


def test_post_with_data_body() -> None:
    """POST with form data delegates correctly."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    client.post("https://example.com/api", data={"field": "value"})

    call_kwargs = mock_httpx.request.call_args[1]
    assert call_kwargs["data"] == {"field": "value"}


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------


def test_close_client() -> None:
    """Verify that close calls close on the underlying client."""
    mock_httpx = MagicMock(spec=httpx.Client)
    client = _make_client(mock_httpx)
    client.close()
    mock_httpx.close.assert_called_once()


def test_close_multiple_times() -> None:
    """Verify that close() can be called multiple times without raising."""
    mock_httpx = MagicMock(spec=httpx.Client)
    client = _make_client(mock_httpx)
    client.close()
    client.close()
    assert mock_httpx.close.call_count == 2


# ---------------------------------------------------------------------------
# Module-level export
# ---------------------------------------------------------------------------


def test_module_level_export() -> None:
    """Verify that the module-level exported instance is correctly initialized."""
    assert isinstance(http_client, HttpClient)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_empty_url_rejected() -> None:
    """Empty URL raises HttpClientError before any network call."""
    client = _make_client()
    with pytest.raises(HttpClientError, match="URL must not be empty"):
        client.get("")


def test_whitespace_url_rejected() -> None:
    """Whitespace-only URL raises HttpClientError."""
    client = _make_client()
    with pytest.raises(HttpClientError, match="URL must not be empty"):
        client.get("   ")


def test_post_empty_url_rejected() -> None:
    """Empty URL on POST raises HttpClientError."""
    client = _make_client()
    with pytest.raises(HttpClientError, match="URL must not be empty"):
        client.post("")


# ---------------------------------------------------------------------------
# Header merging
# ---------------------------------------------------------------------------


def test_default_user_agent_applied() -> None:
    """User-Agent from configuration is applied as a default header."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    client.get("https://example.com")

    call_kwargs = mock_httpx.request.call_args[1]
    assert call_kwargs["headers"]["User-Agent"] == "TestBot/1.0"


def test_per_request_headers_merge() -> None:
    """Per-request headers merge with defaults without removing User-Agent."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    client.get("https://example.com", headers={"Accept": "text/html"})

    call_kwargs = mock_httpx.request.call_args[1]
    assert call_kwargs["headers"]["User-Agent"] == "TestBot/1.0"
    assert call_kwargs["headers"]["Accept"] == "text/html"


def test_per_request_header_overrides_default() -> None:
    """Per-request User-Agent overrides the configured default."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    client.get("https://example.com", headers={"User-Agent": "CustomBot/2.0"})

    call_kwargs = mock_httpx.request.call_args[1]
    assert call_kwargs["headers"]["User-Agent"] == "CustomBot/2.0"


# ---------------------------------------------------------------------------
# Timeout resolution
# ---------------------------------------------------------------------------


def test_timeout_from_config() -> None:
    """Default timeout is read from settings when no override given."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx, **{"scraper.timeout": 42})
    client.get("https://example.com")

    call_kwargs = mock_httpx.request.call_args[1]
    assert call_kwargs["timeout"] == 42


def test_per_request_timeout_override() -> None:
    """Per-request timeout overrides the configured default."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    client.get("https://example.com", timeout=5.0)

    call_kwargs = mock_httpx.request.call_args[1]
    assert call_kwargs["timeout"] == 5.0


# ---------------------------------------------------------------------------
# Exception normalization
# ---------------------------------------------------------------------------


def test_timeout_exception_normalized() -> None:
    """httpx.TimeoutException is normalized to HttpTimeoutError."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.side_effect = httpx.TimeoutException("timed out")

    client = _make_client(mock_httpx)
    with pytest.raises(HttpTimeoutError, match="timed out"):
        client.get("https://example.com")


def test_connection_error_normalized() -> None:
    """httpx.ConnectError is normalized to HttpConnectionError."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.side_effect = httpx.ConnectError("connection refused")

    client = _make_client(mock_httpx)
    with pytest.raises(HttpConnectionError, match="connection failed"):
        client.get("https://example.com")


def test_unexpected_error_normalized() -> None:
    """Other httpx.HTTPError is normalized to HttpClientError."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.side_effect = httpx.DecodingError("decode failure")

    client = _make_client(mock_httpx)
    with pytest.raises(HttpClientError, match="decode failure"):
        client.get("https://example.com")


def test_original_cause_preserved() -> None:
    """Normalized exceptions preserve the original httpx exception as __cause__."""
    mock_httpx = MagicMock(spec=httpx.Client)
    original = httpx.TimeoutException("original")
    mock_httpx.request.side_effect = original

    client = _make_client(mock_httpx)
    with pytest.raises(HttpTimeoutError) as exc_info:
        client.get("https://example.com")

    assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def test_log_debug_on_start() -> None:
    """Verify a DEBUG log is emitted when a request starts."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    with patch("app.core.http_client.logger") as mock_logger:
        client.get("https://example.com")

    mock_logger.debug.assert_called_once()
    call_args = mock_logger.debug.call_args[0]
    assert call_args[1] == "GET"
    assert call_args[2] == "https://example.com"


def test_log_info_on_success() -> None:
    """Verify an INFO log is emitted on successful response."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.return_value = _mock_response()

    client = _make_client(mock_httpx)
    with patch("app.core.http_client.logger") as mock_logger:
        client.get("https://example.com")

    mock_logger.info.assert_called_once()


def test_log_error_on_failure() -> None:
    """Verify an ERROR log is emitted when a request fails."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_httpx.request.side_effect = httpx.TimeoutException("timed out")

    client = _make_client(mock_httpx)
    with patch("app.core.http_client.logger") as mock_logger:
        with pytest.raises(HttpTimeoutError):
            client.get("https://example.com")

    mock_logger.error.assert_called_once()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def test_follow_redirects_config() -> None:
    """follow_redirects from config is applied to the underlying client."""
    with patch("app.core.http_client.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: {
            "scraper.timeout": 30,
            "scraper.user_agent": "TestBot/1.0",
            "http.follow_redirects": False,
        }.get(key, default)
        client = HttpClient()

    assert client._follow_redirects is False
    client.close()
