"""Immutable retry policy configuration.

Defines the parameters controlling retry behavior: maximum attempts,
backoff delays, jitter, and which exceptions are retryable.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.exceptions import HttpConnectionError, HttpTimeoutError

if TYPE_CHECKING:
    pass

__all__ = ["RetryPolicy"]


@dataclass(frozen=True)
class RetryPolicy:
    """Immutable configuration governing retry behavior.

    Uses exponential backoff with optional jitter. Only exceptions
    matching ``retryable_exceptions`` trigger a retry; all others
    propagate immediately.
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (
        HttpTimeoutError,
        HttpConnectionError,
    )

    def __post_init__(self) -> None:
        """Validate policy parameters after initialization.

        Raises:
            ValueError: If any parameter is out of its valid range.
        """
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts must be >= 1, got {self.max_attempts}")
        if self.initial_delay <= 0:
            raise ValueError(f"initial_delay must be > 0, got {self.initial_delay}")
        if self.max_delay < self.initial_delay:
            raise ValueError(
                f"max_delay ({self.max_delay}) must be >= initial_delay "
                f"({self.initial_delay})"
            )

    def get_delay(self, attempt: int) -> float:
        """Calculate the delay before the next retry attempt.

        Uses exponential backoff: ``initial_delay * 2 ** attempt``,
        capped at ``max_delay``. When jitter is enabled, a random
        multiplier between 0.5 and 1.0 is applied.

        Args:
            attempt: Zero-based attempt index (0 = first retry).

        Returns:
            Delay in seconds before the next attempt.
        """
        delay = min(self.initial_delay * (2**attempt), self.max_delay)
        if self.jitter:
            delay *= random.uniform(0.5, 1.0)  # noqa: S311
        return delay

    def is_retryable(self, exc: Exception) -> bool:
        """Determine whether the given exception should trigger a retry.

        Args:
            exc: The exception to evaluate.

        Returns:
            True if the exception is an instance of any retryable type.
        """
        return isinstance(exc, self.retryable_exceptions)
