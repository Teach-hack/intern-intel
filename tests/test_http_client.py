"""Unit tests for the centralized HttpClient class."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx

from app.core.http_client import HttpClient, http_client


def test_default_initialization() -> None:
    """Verify that HttpClient defaults to instantiating an httpx.Client."""
    client = HttpClient()
    assert isinstance(client._client, httpx.Client)
    # Cleanup connection pool resources
    client.close()


def test_dependency_injection() -> None:
    """Verify that a pre-configured httpx.Client can be injected."""
    mock_httpx = MagicMock(spec=httpx.Client)
    client = HttpClient(client=mock_httpx)
    assert client._client is mock_httpx


def test_get_request() -> None:
    """Verify that GET requests correctly delegate parameters to the underlying client."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_httpx.get.return_value = mock_response

    client = HttpClient(client=mock_httpx)
    url = "https://example.com/api"
    params = {"q": "search"}
    headers = {"Authorization": "Bearer token"}

    res = client.get(url, params=params, headers=headers, timeout=10.0)

    assert res is mock_response
    mock_httpx.get.assert_called_once_with(
        url,
        params=params,
        headers=headers,
        timeout=10.0,
    )


def test_post_request() -> None:
    """Verify that POST requests correctly delegate parameters to the underlying client."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_httpx.post.return_value = mock_response

    client = HttpClient(client=mock_httpx)
    url = "https://example.com/api"
    json_data = {"key": "value"}
    headers = {"Content-Type": "application/json"}

    res = client.post(url, json=json_data, headers=headers)

    assert res is mock_response
    mock_httpx.post.assert_called_once_with(
        url,
        json=json_data,
        headers=headers,
    )


def test_close_client() -> None:
    """Verify that close calls close on the underlying client."""
    mock_httpx = MagicMock(spec=httpx.Client)
    client = HttpClient(client=mock_httpx)
    client.close()
    mock_httpx.close.assert_called_once()


def test_module_level_export() -> None:
    """Verify that the module-level exported instance is correctly initialized."""
    assert isinstance(http_client, HttpClient)


def test_close_multiple_times() -> None:
    """Verify that close() can be called multiple times without raising an exception."""
    mock_httpx = MagicMock(spec=httpx.Client)
    client = HttpClient(client=mock_httpx)
    client.close()
    client.close()
    assert mock_httpx.close.call_count == 2


def test_get_request_no_kwargs() -> None:
    """Verify that GET requests work correctly without optional keyword arguments."""
    mock_httpx = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_httpx.get.return_value = mock_response

    client = HttpClient(client=mock_httpx)
    url = "https://example.com/api"

    res = client.get(url)

    assert res is mock_response
    mock_httpx.get.assert_called_once_with(url)
