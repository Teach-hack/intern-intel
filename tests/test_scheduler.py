"""Unit tests for the Scheduler class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.runner import Runner
from app.scheduler import Scheduler


@pytest.fixture
def mock_runner() -> MagicMock:
    """Fixture to provide a mocked Runner."""
    return MagicMock(spec=Runner)


def test_scheduler_initialization(mock_runner: MagicMock) -> None:
    """Verify correct dependency injection in initialization."""
    scheduler = Scheduler(mock_runner, interval_seconds=42)
    assert scheduler._runner is mock_runner
    assert scheduler._interval_seconds == 42
    assert not scheduler._running


def test_scheduler_run_once_success(mock_runner: MagicMock) -> None:
    """Verify run_once executes the runner without exceptions."""
    scheduler = Scheduler(mock_runner)
    with patch("app.scheduler.logger") as mock_logger:
        scheduler.run_once()

    mock_runner.run.assert_called_once()
    mock_logger.info.assert_called_once_with("Executing scheduled pipeline run.")


def test_scheduler_run_once_handles_exception(mock_runner: MagicMock) -> None:
    """Verify run_once logs and does not propagate runner errors."""
    mock_runner.run.side_effect = RuntimeError("Runner crashed")
    scheduler = Scheduler(mock_runner)

    with patch("app.scheduler.logger") as mock_logger:
        scheduler.run_once()

    mock_runner.run.assert_called_once()
    mock_logger.error.assert_called_once_with(
        "Scheduled pipeline execution failed: {}", mock_runner.run.side_effect
    )


@patch("time.sleep")
def test_scheduler_run_forever_loop(
    mock_sleep: MagicMock,
    mock_runner: MagicMock,
) -> None:
    """Verify run_forever runs the loop, calls sleep, and can be stopped."""
    scheduler = Scheduler(mock_runner, interval_seconds=15)

    # Modify self._running to False on the first iteration to terminate loop cleanly
    def mock_run() -> None:
        scheduler._running = False

    mock_runner.run.side_effect = mock_run

    with patch("app.scheduler.logger") as mock_logger:
        scheduler.run_forever()

    mock_runner.run.assert_called_once()
    mock_sleep.assert_called_once_with(15)
    mock_logger.info.assert_any_call("Scheduler started.")
    mock_logger.info.assert_any_call("Scheduler sleeping for {} seconds.", 15)
    mock_logger.info.assert_any_call("Scheduler stopped.")


@patch("time.sleep")
def test_scheduler_run_forever_keyboard_interrupt(
    mock_sleep: MagicMock,
    mock_runner: MagicMock,
) -> None:
    """Verify KeyboardInterrupt terminates the scheduler loop cleanly."""
    scheduler = Scheduler(mock_runner, interval_seconds=10)

    # Force a KeyboardInterrupt on the runner execution
    mock_runner.run.side_effect = KeyboardInterrupt()

    with patch("app.scheduler.logger") as mock_logger:
        scheduler.run_forever()

    mock_runner.run.assert_called_once()
    mock_sleep.assert_not_called()
    mock_logger.info.assert_any_call("Scheduler interrupted by user.")
    mock_logger.info.assert_any_call("Scheduler stopped.")
