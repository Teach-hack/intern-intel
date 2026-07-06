"""Centralized HTTP client for the InternIntel application.

This module provides a minimal wrapper around ``httpx`` to manage transport,
connection sharing, and basic request execution.
"""

from __future__ import annotations

from typing import Any

import httpx

__all__ = ["HttpClient", "http_client"]


class HttpClient:
    """Centralized HTTP client utilizing a shared connection pool."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Initialize the HTTP client.

        Args:
            client: Optional preconfigured ``httpx.Client`` instance to use
                (e.g., for dependency injection during testing).
        """
        if client is None:
            self._client = httpx.Client()
        else:
            self._client = client

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform an HTTP GET request.

        Args:
            url: Target URL.
            **kwargs: Additional keyword arguments forwarded to the
                underlying ``httpx.Client.get`` call.

        Returns:
            The HTTP response object.
        """
        return self._client.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform an HTTP POST request.

        Args:
            url: Target URL.
            **kwargs: Additional keyword arguments forwarded to the
                underlying ``httpx.Client.post`` call.

        Returns:
            The HTTP response object.
        """
        return self._client.post(url, **kwargs)

    def close(self) -> None:
        """Release underlying connections and clean up resources."""
        self._client.close()


# The default, shared application-wide HTTP client instance.
# Scrapers, connectors, and services should reuse this singleton
# instance to benefit from connection pool reuse and keep-alive.
http_client = HttpClient()
