"""Unit tests for the RateLimiter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.rate_limiter import RateLimiter

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_default_construction() -> None:
    """Verify default RateLimiter is created without error."""
    limiter = RateLimiter()
    assert limiter._min_interval == 0.5  # 1 / 2.0


def test_custom_rate() -> None:
    """Verify custom requests_per_second sets the correct interval."""
    limiter = RateLimiter(requests_per_second=10.0)
    assert limiter._min_interval == pytest.approx(0.1)


def test_invalid_rate_raises() -> None:
    """Zero or negative requests_per_second raises ValueError."""
    with pytest.raises(ValueError, match="requests_per_second must be > 0"):
        RateLimiter(requests_per_second=0)

    with pytest.raises(ValueError, match="requests_per_second must be > 0"):
        RateLimiter(requests_per_second=-1.0)


# ---------------------------------------------------------------------------
# First request — no sleep
# ---------------------------------------------------------------------------


def test_first_request_no_sleep() -> None:
    """First request to any domain should not trigger a sleep."""
    mock_sleep = MagicMock()
    limiter = RateLimiter(sleep_func=mock_sleep)

    limiter.acquire("api.example.com")

    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Second request — within window
# ---------------------------------------------------------------------------


def test_second_request_within_window_sleeps() -> None:
    """Second request within the min interval window triggers sleep."""
    mock_sleep = MagicMock()
    limiter = RateLimiter(requests_per_second=2.0, sleep_func=mock_sleep)

    # Simulate: first request at time=0, second at time=0.1
    # min_interval = 0.5, so remaining = 0.4
    with patch("app.core.rate_limiter.time") as mock_time:
        mock_time.monotonic.side_effect = [0.0, 0.1, 0.5]
        limiter.acquire("example.com")
        limiter.acquire("example.com")

    mock_sleep.assert_called_once()
    sleep_duration = mock_sleep.call_args[0][0]
    assert sleep_duration == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# Second request — after window
# ---------------------------------------------------------------------------


def test_second_request_after_window_no_sleep() -> None:
    """Second request after the min interval has passed does not sleep."""
    mock_sleep = MagicMock()
    limiter = RateLimiter(requests_per_second=2.0, sleep_func=mock_sleep)

    # min_interval = 0.5, elapsed = 1.0 > 0.5
    with patch("app.core.rate_limiter.time") as mock_time:
        mock_time.monotonic.side_effect = [0.0, 1.0]
        limiter.acquire("example.com")
        limiter.acquire("example.com")

    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Per-domain independence
# ---------------------------------------------------------------------------


def test_per_domain_independence() -> None:
    """Different domains are rate-limited independently."""
    mock_sleep = MagicMock()
    limiter = RateLimiter(requests_per_second=2.0, sleep_func=mock_sleep)

    # Two different domains in quick succession — no sleep needed
    with patch("app.core.rate_limiter.time") as mock_time:
        mock_time.monotonic.side_effect = [0.0, 0.0]
        limiter.acquire("domain-a.com")
        limiter.acquire("domain-b.com")

    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Multiple requests — ordering
# ---------------------------------------------------------------------------


def test_multiple_requests_ordering() -> None:
    """Multiple requests to the same domain are rate-limited correctly."""
    mock_sleep = MagicMock()
    limiter = RateLimiter(requests_per_second=1.0, sleep_func=mock_sleep)

    # min_interval = 1.0
    # Request 1: t=0 (no sleep)
    # Request 2: t=0.2, needs sleep 0.8, post-sleep now=1.0
    # Request 3: t=1.5, elapsed=0.5 from 1.0, needs sleep 0.5, post-sleep now=2.0
    with patch("app.core.rate_limiter.time") as mock_time:
        mock_time.monotonic.side_effect = [0.0, 0.2, 1.0, 1.5, 2.0]
        limiter.acquire("example.com")
        limiter.acquire("example.com")
        limiter.acquire("example.com")

    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] == pytest.approx(0.8)
    assert mock_sleep.call_args_list[1][0][0] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def test_logs_debug_on_wait() -> None:
    """A debug log is emitted when the rate limiter causes a wait."""
    mock_sleep = MagicMock()
    limiter = RateLimiter(requests_per_second=2.0, sleep_func=mock_sleep)

    with patch("app.core.rate_limiter.time") as mock_time:
        mock_time.monotonic.side_effect = [0.0, 0.1, 0.5]
        with patch("app.core.rate_limiter.logger") as mock_logger:
            limiter.acquire("example.com")
            limiter.acquire("example.com")

    mock_logger.debug.assert_called_once()
    debug_args = mock_logger.debug.call_args[0]
    assert "example.com" in debug_args[0].format(*debug_args[1:])
