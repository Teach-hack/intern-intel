"""Centralized HTTP client for the InternIntel application.

This module provides a production-ready wrapper around ``httpx`` to manage
transport, connection sharing, configuration, logging, exception
normalization, retry, and rate limiting.

All outbound HTTP traffic in the application must flow through this client.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpRetryExhaustedError,
    HttpStatusError,
    HttpTimeoutError,
)
from app.core.logger import logger
from app.core.rate_limiter import RateLimiter
from app.core.retry import RetryExecutor
from app.core.retry_policy import RetryPolicy

__all__ = ["HttpClient", "http_client"]

# Documented built-in defaults (lowest priority in configuration resolution).
_DEFAULT_TIMEOUT: int = 30
_DEFAULT_USER_AGENT: str = "InternIntelBot/1.0"
_DEFAULT_FOLLOW_REDIRECTS: bool = True

# HTTP status codes that should trigger a retry.
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


_UNSET = object()


class HttpClient:
    """Centralized HTTP client utilizing a shared connection pool.

    Reads configuration from ``app.core.config.settings`` and applies
    consistent timeouts, User-Agent headers, logging, retry, and rate
    limiting across all requests.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        retry_policy: RetryPolicy | None | object = _UNSET,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Initialize the HTTP client.

        Args:
            client: Optional preconfigured ``httpx.Client`` instance to use
                (e.g., for dependency injection during testing).
            retry_policy: Retry policy for transient failures. Pass
                ``None`` to disable retry entirely. Defaults to a
                standard policy retrying ``HttpTimeoutError``,
                ``HttpConnectionError``, and ``HttpStatusError``.
            rate_limiter: Per-domain rate limiter. Defaults to a
                conservative 2 req/s limiter.
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

        # Retry policy: default retries timeout, connection, and status errors.
        if retry_policy is _UNSET:
            self._retry_policy: RetryPolicy | None = RetryPolicy(
                retryable_exceptions=(
                    HttpTimeoutError,
                    HttpConnectionError,
                    HttpStatusError,
                ),
            )
        else:
            self._retry_policy = retry_policy  # type: ignore[assignment]

        # Rate limiter: default to 2 requests/second per domain.
        self._rate_limiter = rate_limiter or RateLimiter()

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
            HttpRetryExhaustedError: When all retries are exhausted.
        """
        return self._request_with_retry("GET", url, **kwargs)

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
            HttpRetryExhaustedError: When all retries are exhausted.
        """
        return self._request_with_retry("POST", url, **kwargs)

    def close(self) -> None:
        """Release underlying connections and clean up resources."""
        self._client.close()

    def _request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        """Execute a request with retry and rate limiting.

        Args:
            method: HTTP method (e.g. ``GET``, ``POST``).
            url: Target URL.
            **kwargs: Additional arguments forwarded to ``_request``.

        Returns:
            The HTTP response object.

        Raises:
            HttpRetryExhaustedError: When all retries are exhausted.
            HttpClientError: On non-retryable failures.
        """
        # Rate limit before the first attempt.
        domain = urlparse(url).netloc or url
        self._rate_limiter.acquire(domain)

        if self._retry_policy is None:
            return self._request(method, url, **kwargs)

        executor = RetryExecutor(policy=self._retry_policy)
        try:
            return executor.execute(lambda: self._request(method, url, **kwargs))
        except (HttpTimeoutError, HttpConnectionError, HttpStatusError) as exc:
            raise HttpRetryExhaustedError(
                f"{method} {url} failed after "
                f"{self._retry_policy.max_attempts} attempts: {exc}"
            ) from exc

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
            HttpStatusError: When the response has a retryable status code.
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

            # Raise on retryable status codes so the retry executor catches them.
            if response.status_code in _RETRYABLE_STATUS_CODES:
                raise HttpStatusError(
                    f"{method} {url} returned {response.status_code}",
                    status_code=response.status_code,
                    url=url,
                    method=method,
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
