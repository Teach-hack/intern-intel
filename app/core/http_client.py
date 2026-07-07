"""Centralized HTTP client for the InternIntel application.

This module provides a production-ready wrapper around ``httpx`` to manage
transport, connection sharing, configuration, logging, and exception
normalization.

All outbound HTTP traffic in the application must flow through this client.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpTimeoutError,
)
from app.core.logger import logger

__all__ = ["HttpClient", "http_client"]

# Documented built-in defaults (lowest priority in configuration resolution).
_DEFAULT_TIMEOUT: int = 30
_DEFAULT_USER_AGENT: str = "InternIntelBot/1.0"
_DEFAULT_FOLLOW_REDIRECTS: bool = True


class HttpClient:
    """Centralized HTTP client utilizing a shared connection pool.

    Reads configuration from ``app.core.config.settings`` and applies
    consistent timeouts, User-Agent headers, and logging across all
    requests.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Initialize the HTTP client.

        Args:
            client: Optional preconfigured ``httpx.Client`` instance to use
                (e.g., for dependency injection during testing).
        """
        self._timeout: int = settings.get("scraper.timeout", _DEFAULT_TIMEOUT)
        self._user_agent: str = settings.get("scraper.user_agent", _DEFAULT_USER_AGENT)
        self._follow_redirects: bool = settings.get(
            "http.follow_redirects", _DEFAULT_FOLLOW_REDIRECTS
        )

        if client is None:
            self._client = httpx.Client(
                timeout=self._timeout,
                headers={"User-Agent": self._user_agent},
                follow_redirects=self._follow_redirects,
            )
        else:
            self._client = client

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform an HTTP GET request.

        Args:
            url: Target URL.
            **kwargs: Additional keyword arguments forwarded to the
                underlying ``httpx.Client.request`` call.

        Returns:
            The HTTP response object.

        Raises:
            HttpClientError: On any client failure.
            HttpTimeoutError: When the request exceeds the configured timeout.
            HttpConnectionError: When the connection cannot be established.
        """
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform an HTTP POST request.

        Args:
            url: Target URL.
            **kwargs: Additional keyword arguments forwarded to the
                underlying ``httpx.Client.request`` call.

        Returns:
            The HTTP response object.

        Raises:
            HttpClientError: On any client failure.
            HttpTimeoutError: When the request exceeds the configured timeout.
            HttpConnectionError: When the connection cannot be established.
        """
        return self._request("POST", url, **kwargs)

    def close(self) -> None:
        """Release underlying connections and clean up resources."""
        self._client.close()

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Execute the request lifecycle with validation, logging, and
        exception normalization.

        Args:
            method: HTTP method (e.g. ``GET``, ``POST``).
            url: Target URL.
            **kwargs: Additional arguments forwarded to
                ``httpx.Client.request``.

        Returns:
            The HTTP response object.

        Raises:
            HttpClientError: On any client failure.
            HttpTimeoutError: When the request exceeds the configured timeout.
            HttpConnectionError: When the connection cannot be established.
        """
        # --- Validate Input ---
        if not url or not url.strip():
            raise HttpClientError("URL must not be empty")

        # --- Merge Headers ---
        merged_headers: dict[str, str] = {"User-Agent": self._user_agent}
        request_headers = kwargs.pop("headers", None)
        if request_headers:
            merged_headers.update(request_headers)
        kwargs["headers"] = merged_headers

        # --- Resolve Timeout ---
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self._timeout

        # --- Log Request Start ---
        logger.debug("{} {}", method, url)

        try:
            start = time.monotonic()
            response = self._client.request(method, url, **kwargs)
            elapsed_ms = (time.monotonic() - start) * 1000

            logger.info(
                "{} {} — {} ({:.0f}ms)",
                method,
                url,
                response.status_code,
                elapsed_ms,
            )
            return response

        except httpx.TimeoutException as exc:
            logger.error("{} {} timed out: {}", method, url, exc)
            raise HttpTimeoutError(f"{method} {url} timed out") from exc

        except httpx.ConnectError as exc:
            logger.error("{} {} connection failed: {}", method, url, exc)
            raise HttpConnectionError(f"{method} {url} connection failed") from exc

        except httpx.HTTPError as exc:
            logger.error("{} {} failed: {}", method, url, exc)
            raise HttpClientError(f"{method} {url} failed: {exc}") from exc


# The default, shared application-wide HTTP client instance.
# Scrapers, connectors, and services should reuse this singleton
# instance to benefit from connection pool reuse and keep-alive.
http_client = HttpClient()
