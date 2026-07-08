"""Retry execution engine.

Provides a ``RetryExecutor`` that wraps callable invocations with
configurable retry logic driven by a :class:`RetryPolicy`.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from app.core.logger import logger
from app.core.retry_policy import RetryPolicy

__all__ = ["RetryExecutor"]

T = TypeVar("T")


class RetryExecutor:
    """Execute callables with automatic retry on transient failures.

    Uses a :class:`RetryPolicy` to determine backoff delays and which
    exceptions are retryable. Non-retryable exceptions propagate
    immediately without consuming retry attempts.
    """

    def __init__(
        self,
        policy: RetryPolicy | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize the retry executor.

        Args:
            policy: Retry policy governing behavior. Defaults to the
                standard ``RetryPolicy()``.
            sleep_func: Callable used for sleeping between attempts.
                Injected for testability.
        """
        self._policy = policy or RetryPolicy()
        self._sleep = sleep_func

    def execute(self, func: Callable[[], T]) -> T:
        """Execute a callable with retry logic.

        Args:
            func: Zero-argument callable to execute.

        Returns:
            The return value of ``func`` on success.

        Raises:
            Exception: The last exception raised after all retries are
                exhausted, or a non-retryable exception immediately.
        """
        last_exc: Exception | None = None

        for attempt in range(self._policy.max_attempts):
            try:
                result = func()
                if attempt > 0:
                    logger.info(
                        "Retry successful on attempt {}/{}",
                        attempt + 1,
                        self._policy.max_attempts,
                    )
                return result

            except Exception as exc:
                if not self._policy.is_retryable(exc):
                    raise

                last_exc = exc
                remaining = self._policy.max_attempts - attempt - 1

                if remaining > 0:
                    delay = self._policy.get_delay(attempt)
                    logger.warning(
                        "Attempt {}/{} failed ({}). Retrying in {:.2f}s...",
                        attempt + 1,
                        self._policy.max_attempts,
                        exc,
                        delay,
                    )
                    self._sleep(delay)
                else:
                    logger.error(
                        "All {} retry attempts exhausted. Last error: {}",
                        self._policy.max_attempts,
                        exc,
                    )

        # All attempts exhausted — re-raise the last exception.
        assert last_exc is not None  # noqa: S101
        raise last_exc
