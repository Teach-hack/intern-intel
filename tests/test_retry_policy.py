"""Unit tests for the RetryPolicy dataclass."""

from __future__ import annotations

import pytest

from app.core.exceptions import HttpConnectionError, HttpTimeoutError
from app.core.retry_policy import RetryPolicy

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_default_construction() -> None:
    """Verify default values are applied correctly."""
    policy = RetryPolicy()

    assert policy.max_attempts == 3
    assert policy.initial_delay == 1.0
    assert policy.max_delay == 30.0
    assert policy.jitter is True
    assert HttpTimeoutError in policy.retryable_exceptions
    assert HttpConnectionError in policy.retryable_exceptions


def test_custom_construction() -> None:
    """Verify custom parameters are stored correctly."""
    policy = RetryPolicy(
        max_attempts=5,
        initial_delay=0.5,
        max_delay=10.0,
        jitter=False,
        retryable_exceptions=(ValueError,),
    )

    assert policy.max_attempts == 5
    assert policy.initial_delay == 0.5
    assert policy.max_delay == 10.0
    assert policy.jitter is False
    assert policy.retryable_exceptions == (ValueError,)


def test_immutability() -> None:
    """Verify frozen dataclass prevents attribute mutation."""
    policy = RetryPolicy()
    with pytest.raises(AttributeError):
        policy.max_attempts = 10  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_max_attempts_below_one_raises() -> None:
    """max_attempts < 1 raises ValueError."""
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        RetryPolicy(max_attempts=0)


def test_negative_max_attempts_raises() -> None:
    """Negative max_attempts raises ValueError."""
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        RetryPolicy(max_attempts=-1)


def test_zero_initial_delay_raises() -> None:
    """initial_delay = 0 raises ValueError."""
    with pytest.raises(ValueError, match="initial_delay must be > 0"):
        RetryPolicy(initial_delay=0)


def test_negative_initial_delay_raises() -> None:
    """Negative initial_delay raises ValueError."""
    with pytest.raises(ValueError, match="initial_delay must be > 0"):
        RetryPolicy(initial_delay=-1.0)


def test_max_delay_below_initial_raises() -> None:
    """max_delay < initial_delay raises ValueError."""
    with pytest.raises(ValueError, match="max_delay .* must be >= initial_delay"):
        RetryPolicy(initial_delay=5.0, max_delay=2.0)


# ---------------------------------------------------------------------------
# get_delay — without jitter
# ---------------------------------------------------------------------------


def test_get_delay_exponential_backoff_no_jitter() -> None:
    """Delays follow exponential backoff when jitter is disabled."""
    policy = RetryPolicy(initial_delay=1.0, max_delay=30.0, jitter=False)

    assert policy.get_delay(0) == 1.0
    assert policy.get_delay(1) == 2.0
    assert policy.get_delay(2) == 4.0
    assert policy.get_delay(3) == 8.0


def test_get_delay_capped_at_max_no_jitter() -> None:
    """Delay never exceeds max_delay."""
    policy = RetryPolicy(initial_delay=1.0, max_delay=5.0, jitter=False)

    assert policy.get_delay(10) == 5.0


# ---------------------------------------------------------------------------
# get_delay — with jitter
# ---------------------------------------------------------------------------


def test_get_delay_with_jitter_in_range() -> None:
    """Jittered delay is between 50% and 100% of the base delay."""
    policy = RetryPolicy(initial_delay=2.0, max_delay=30.0, jitter=True)

    for attempt in range(5):
        base = min(2.0 * (2**attempt), 30.0)
        delay = policy.get_delay(attempt)
        assert base * 0.5 <= delay <= base


# ---------------------------------------------------------------------------
# is_retryable
# ---------------------------------------------------------------------------


def test_is_retryable_matching_exception() -> None:
    """Matching exception returns True."""
    policy = RetryPolicy()
    assert policy.is_retryable(HttpTimeoutError("timeout")) is True


def test_is_retryable_non_matching_exception() -> None:
    """Non-matching exception returns False."""
    policy = RetryPolicy()
    assert policy.is_retryable(ValueError("bad value")) is False


def test_is_retryable_subclass() -> None:
    """Subclass of retryable exception returns True."""

    class CustomTimeout(HttpTimeoutError):
        pass

    policy = RetryPolicy()
    assert policy.is_retryable(CustomTimeout("custom")) is True


def test_is_retryable_custom_exceptions() -> None:
    """Custom retryable exception tuple is respected."""
    policy = RetryPolicy(retryable_exceptions=(KeyError,))
    assert policy.is_retryable(KeyError("key")) is True
    assert policy.is_retryable(HttpTimeoutError("timeout")) is False
