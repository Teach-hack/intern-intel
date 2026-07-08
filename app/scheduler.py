"""Interval-based scheduler for periodic execution of the application runner."""

from __future__ import annotations

import time

from app.core.logger import logger
from app.runner import Runner

__all__ = ["Scheduler"]


class Scheduler:
    """Runs the application execution Runner on a configured interval."""

    def __init__(self, runner: Runner, interval_seconds: int = 3600) -> None:
        """Initialize the Scheduler.

        Args:
            runner: Injectable application Runner instance.
            interval_seconds: Delay in seconds between pipeline runs.
        """
        self._runner = runner
        self._interval_seconds = interval_seconds
        self._running = False

    def run_once(self) -> None:
        """Execute a single pipeline run once, catching exceptions."""
        try:
            logger.info("Executing scheduled pipeline run.")
            self._runner.run()
        except Exception as exc:
            logger.error("Scheduled pipeline execution failed: {}", exc)

    def run_forever(self) -> None:
        """Execute the runner periodically in a loop until stopped."""
        logger.info("Scheduler started.")
        self._running = True
        try:
            while self._running:
                self.run_once()
                logger.info(
                    "Scheduler sleeping for {} seconds.", self._interval_seconds
                )
                time.sleep(self._interval_seconds)
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user.")
        finally:
            self._running = False
            logger.info("Scheduler stopped.")
