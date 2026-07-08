"""Per-domain request rate limiter.

Enforces a configurable maximum request rate per domain using
monotonic clock tracking and thread-safe locking.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from app.core.logger import logger

__all__ = ["RateLimiter"]


class RateLimiter:
    """Thread-safe per-domain rate limiter.

    Tracks the last request timestamp for each domain and sleeps
    only when the minimum interval has not elapsed.
    """

    def __init__(
        self,
        requests_per_second: float = 2.0,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            requests_per_second: Maximum allowed requests per second
                per domain.
            sleep_func: Callable used for sleeping. Injected for
                testability.

        Raises:
            ValueError: If ``requests_per_second`` is not positive.
        """
        if requests_per_second <= 0:
            raise ValueError(
                f"requests_per_second must be > 0, got {requests_per_second}"
            )
        self._min_interval: float = 1.0 / requests_per_second
        self._sleep = sleep_func
        self._last_request_times: dict[str, float] = {}
        self._lock = threading.Lock()

    def acquire(self, domain: str) -> None:
        """Block until a request to the given domain is permitted.

        If enough time has elapsed since the last request to this
        domain, returns immediately. Otherwise, sleeps for the
        remaining interval.

        Args:
            domain: The target domain (e.g. ``"api.greenhouse.io"``).
        """
        with self._lock:
            now = time.monotonic()
            last_time = self._last_request_times.get(domain)

            if last_time is not None:
                elapsed = now - last_time
                remaining = self._min_interval - elapsed

                if remaining > 0:
                    logger.debug(
                        "Rate limiter: sleeping {:.3f}s for domain '{}'",
                        remaining,
                        domain,
                    )
                    self._sleep(remaining)
                    now = time.monotonic()

            self._last_request_times[domain] = now
