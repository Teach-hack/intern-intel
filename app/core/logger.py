"""Application logging configuration."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

from loguru import logger as _logger

from app.core.config import settings

if TYPE_CHECKING:
    from loguru._logger import Logger

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_FILE = _LOG_DIR / "internintel.log"

_DEFAULT_LOG_LEVEL: Final[str] = "INFO"

_VALID_LOG_LEVELS: Final[set[str]] = {
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
}

_LOG_FORMAT: Final[str] = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level:<8} | "
    "{name}:{function}:{line} | "
    "{message}"
)

_FILE_ROTATION: Final[str] = "10 MB"
_FILE_RETENTION: Final[str] = "30 days"
_FILE_ENCODING: Final[str] = "utf-8"


def _resolve_log_level() -> str:
    """Resolve and validate the configured logging level.

    Returns:
        A valid Loguru logging level.

    Raises:
        ValueError: If an unsupported logging level is configured.
    """
    level = str(settings.get("logging.level", _DEFAULT_LOG_LEVEL)).upper()

    if level not in _VALID_LOG_LEVELS:
        raise ValueError(
            f"Invalid logging level '{level}'. "
            f"Supported levels: {', '.join(sorted(_VALID_LOG_LEVELS))}"
        )

    return level


def _add_console_sink(log_level: str) -> None:
    """Configure console logging.

    Args:
        log_level: Minimum log level.
    """
    _logger.add(
        sys.stderr,
        level=log_level,
        format=_LOG_FORMAT,
        backtrace=True,
        diagnose=True,
    )


def _add_file_sink(log_level: str) -> None:
    """Configure rotating file logging.

    Args:
        log_level: Minimum log level.
    """
    _logger.add(
        _LOG_FILE,
        level=log_level,
        format=_LOG_FORMAT,
        rotation=_FILE_ROTATION,
        retention=_FILE_RETENTION,
        encoding=_FILE_ENCODING,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )


def _configure_logger() -> Logger:
    """Configure and return the application logger.

    Returns:
        Configured Loguru logger instance.
    """
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_level = _resolve_log_level()

    _logger.remove()

    _add_console_sink(log_level)
    _add_file_sink(log_level)

    return _logger


logger: Logger = _configure_logger()
