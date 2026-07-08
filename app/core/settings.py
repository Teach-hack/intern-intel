"""Strongly typed application settings configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

__all__ = ["Settings"]


class Settings:
    """Strongly typed configuration container with environment override capability."""

    def __init__(self, settings_dict: dict[str, Any] | None = None) -> None:
        """Initialize Settings with raw config dictionary or defaults.

        Args:
            settings_dict: Dict containing settings data. If None, loaded from yaml.
        """
        if settings_dict is None:
            settings_dict = self._load_yaml_config()
        self._raw_config = settings_dict or {}

    def _load_yaml_config(self) -> dict[str, Any]:
        """Load configuration from the settings.yaml file.

        Returns:
            Dictionary loaded from the YAML file.
        """
        config_path = (
            Path(__file__).resolve().parent.parent / "config" / "settings.yaml"
        )
        if not config_path.is_file():
            return {}
        try:
            with config_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a nested config value using dot-notation, checking env variables first.

        Args:
            key: Dot-delimited nested key (e.g. "database.path").
            default: Fallback value if key is not found.

        Returns:
            The setting value.
        """
        # Env variables take precedence, formatted like "DATABASE_PATH"
        env_key = key.replace(".", "_").upper()
        if env_key in os.environ:
            return os.environ[env_key]

        data = self._raw_config
        for part in key.split("."):
            if not isinstance(data, dict) or part not in data:
                return default
            data = data[part]
        return data

    def reload(self) -> None:
        """Reload settings from configuration file."""
        self._raw_config = self._load_yaml_config()

    @property
    def telegram_bot_token(self) -> str | None:
        """Telegram bot token."""
        val = os.environ.get("TELEGRAM_BOT_TOKEN") or self.get(
            "notification.telegram_bot_token"
        )
        return str(val) if val is not None else None

    @property
    def telegram_chat_id(self) -> str | None:
        """Telegram chat ID."""
        val = os.environ.get("TELEGRAM_CHAT_ID") or self.get(
            "notification.telegram_chat_id"
        )
        return str(val) if val is not None else None

    @property
    def telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled."""
        val = os.environ.get("TELEGRAM_ENABLED") or self.get(
            "notification.telegram", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def database_url(self) -> str:
        """Get the database connection URL."""
        env_url = os.environ.get("DATABASE_URL")
        if env_url is not None:
            return env_url

        db_url = self.get("database.url")
        if db_url is not None:
            return str(db_url)

        db_path = self.get("database.path")
        if db_path is not None:
            db_path_str = str(db_path).strip()
            if not db_path_str:
                return ""
            if "://" in db_path_str:
                return db_path_str
            return f"sqlite:///{db_path_str}"

        return "sqlite:///data/database/internships.db"

    @property
    def database_auto_upgrade(self) -> bool:
        """Whether to automatically upgrade the database schema on startup."""
        val = os.environ.get("DATABASE_AUTO_UPGRADE") or self.get(
            "database.auto_upgrade", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def scheduler_interval_seconds(self) -> int:
        """Sleep interval in seconds between scraper runs."""
        val = os.environ.get("SCHEDULER_INTERVAL_SECONDS") or self.get(
            "scheduler.interval_seconds", 3600
        )
        try:
            return int(val)
        except (ValueError, TypeError):
            return 3600

    @property
    def logging_level(self) -> str:
        """Logging severity threshold."""
        val = os.environ.get("LOGGING_LEVEL") or self.get("logging.level", "INFO")
        return str(val).upper()

    @property
    def scraper_timeout(self) -> int:
        """HTTP scraper request timeout limit in seconds."""
        val = os.environ.get("SCRAPER_TIMEOUT") or self.get("scraper.timeout", 30)
        try:
            return int(val)
        except (ValueError, TypeError):
            return 30

    @property
    def scraper_user_agent(self) -> str:
        """HTTP request User-Agent header."""
        val = os.environ.get("SCRAPER_USER_AGENT") or self.get(
            "scraper.user_agent", "InternIntelBot/1.0"
        )
        return str(val)

    @property
    def http_follow_redirects(self) -> bool:
        """HTTP redirects config."""
        val = os.environ.get("HTTP_FOLLOW_REDIRECTS") or self.get(
            "http.follow_redirects", True
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def greenhouse_board_token(self) -> str:
        """Greenhouse board token."""
        val = os.environ.get("GREENHOUSE_BOARD_TOKEN") or self.get(
            "scrapers.greenhouse.board_token", "google"
        )
        return str(val)

    @property
    def lever_site_slug(self) -> str:
        """Lever board slug."""
        val = os.environ.get("LEVER_SITE_SLUG") or self.get(
            "scrapers.lever.site_slug", "veriff"
        )
        return str(val)
