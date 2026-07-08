"""Unit tests for the RetryExecutor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import HttpConnectionError, HttpTimeoutError
from app.core.retry import RetryExecutor
from app.core.retry_policy import RetryPolicy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_executor(
    max_attempts: int = 3,
    jitter: bool = False,
    initial_delay: float = 1.0,
    retryable_exceptions: tuple[type[Exception], ...] = (
        HttpTimeoutError,
        HttpConnectionError,
    ),
) -> tuple[RetryExecutor, MagicMock]:
    """Build a RetryExecutor with a mock sleep function.

    Returns:
        Tuple of (executor, mock_sleep).
    """
    mock_sleep = MagicMock()
    policy = RetryPolicy(
        max_attempts=max_attempts,
        jitter=jitter,
        initial_delay=initial_delay,
        retryable_exceptions=retryable_exceptions,
    )
    executor = RetryExecutor(policy=policy, sleep_func=mock_sleep)
    return executor, mock_sleep


# ---------------------------------------------------------------------------
# Success scenarios
# ---------------------------------------------------------------------------


def test_immediate_success() -> None:
    """Function succeeds on first call — no retries, no sleep."""
    executor, mock_sleep = _make_executor()
    result = executor.execute(lambda: "ok")

    assert result == "ok"
    mock_sleep.assert_not_called()


def test_success_after_one_failure() -> None:
    """Function fails once then succeeds on retry."""
    call_count = 0

    def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise HttpTimeoutError("timeout")
        return "recovered"

    executor, mock_sleep = _make_executor()
    result = executor.execute(flaky)

    assert result == "recovered"
    assert call_count == 2
    mock_sleep.assert_called_once()


def test_success_after_two_failures() -> None:
    """Function fails twice then succeeds."""
    call_count = 0

    def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise HttpConnectionError("connection lost")
        return "recovered"

    executor, mock_sleep = _make_executor(max_attempts=3)
    result = executor.execute(flaky)

    assert result == "recovered"
    assert call_count == 3
    assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# Failure scenarios
# ---------------------------------------------------------------------------


def test_max_retries_exhausted() -> None:
    """All retries exhausted raises the last exception."""
    executor, mock_sleep = _make_executor(max_attempts=3)

    with pytest.raises(HttpTimeoutError, match="timeout"):
        executor.execute(MagicMock(side_effect=HttpTimeoutError("timeout")))

    # 3 attempts, 2 sleeps (no sleep after the last failure)
    assert mock_sleep.call_count == 2


def test_non_retryable_exception_propagates_immediately() -> None:
    """Non-retryable exceptions propagate without consuming retries."""
    executor, mock_sleep = _make_executor()

    with pytest.raises(ValueError, match="bad input"):
        executor.execute(MagicMock(side_effect=ValueError("bad input")))

    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Sleep delays
# ---------------------------------------------------------------------------


def test_sleep_called_with_correct_delay() -> None:
    """Verify exponential backoff delays are passed to sleep."""
    call_count = 0

    def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise HttpTimeoutError("timeout")
        return "ok"

    executor, mock_sleep = _make_executor(
        max_attempts=3, initial_delay=2.0, jitter=False
    )
    executor.execute(flaky)

    # First retry: delay = 2.0 * 2^0 = 2.0
    # Second retry: delay = 2.0 * 2^1 = 4.0
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] == 2.0
    assert mock_sleep.call_args_list[1][0][0] == 4.0


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def test_logs_warning_on_retry() -> None:
    """A warning is logged on each retry attempt."""
    call_count = 0

    def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise HttpTimeoutError("timeout")
        return "ok"

    executor, _ = _make_executor(jitter=False)

    with patch("app.core.retry.logger") as mock_logger:
        executor.execute(flaky)

    mock_logger.warning.assert_called_once()
    warning_args = mock_logger.warning.call_args[0]
    assert "1/3" in warning_args[0].format(*warning_args[1:])


def test_logs_error_on_exhaustion() -> None:
    """An error is logged when all retries are exhausted."""
    executor, _ = _make_executor(max_attempts=2, jitter=False)

    with patch("app.core.retry.logger") as mock_logger:
        with pytest.raises(HttpTimeoutError):
            executor.execute(MagicMock(side_effect=HttpTimeoutError("timeout")))

    mock_logger.error.assert_called_once()


def test_logs_info_on_successful_retry() -> None:
    """An info log is emitted when a retry succeeds."""
    call_count = 0

    def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise HttpTimeoutError("timeout")
        return "ok"

    executor, _ = _make_executor(jitter=False)

    with patch("app.core.retry.logger") as mock_logger:
        executor.execute(flaky)

    mock_logger.info.assert_called_once()
    info_args = mock_logger.info.call_args[0]
    assert "2/3" in info_args[0].format(*info_args[1:])


# ---------------------------------------------------------------------------
# Traceback preservation
# ---------------------------------------------------------------------------


def test_original_traceback_preserved() -> None:
    """The original exception traceback is preserved on exhaustion."""
    executor, _ = _make_executor(max_attempts=1)

    with pytest.raises(HttpTimeoutError) as exc_info:
        executor.execute(MagicMock(side_effect=HttpTimeoutError("original")))

    assert exc_info.value.__traceback__ is not None
