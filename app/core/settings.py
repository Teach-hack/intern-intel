"""Strongly typed application settings configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import sys
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file at startup (skip during testing to prevent env pollution)
if "pytest" not in sys.modules:
    load_dotenv()

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
    def greenhouse_enabled(self) -> bool:
        """Check if Greenhouse scraper is enabled."""
        val = os.environ.get("GREENHOUSE_ENABLED") or self.get(
            "scrapers.greenhouse.enabled", True
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def lever_site_slug(self) -> str:
        """Lever site slug."""
        val = os.environ.get("LEVER_SITE_SLUG") or self.get(
            "scrapers.lever.site_slug", "veriff"
        )
        return str(val)

    @property
    def lever_enabled(self) -> bool:
        """Check if Lever scraper is enabled."""
        val = os.environ.get("LEVER_ENABLED") or self.get(
            "scrapers.lever.enabled", True
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def workday_tenant(self) -> str:
        """Workday tenant ID."""
        val = os.environ.get("WORKDAY_TENANT") or self.get(
            "scrapers.workday.tenant", ""
        )
        return str(val)

    @property
    def workday_parent_site_id(self) -> str:
        """Workday parent site ID."""
        val = os.environ.get("WORKDAY_PARENT_SITE_ID") or self.get(
            "scrapers.workday.parent_site_id", ""
        )
        return str(val)

    @property
    def workday_enabled(self) -> bool:
        """Check if Workday scraper is enabled."""
        val = os.environ.get("WORKDAY_ENABLED") or self.get(
            "scrapers.workday.enabled", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def ashby_company_id(self) -> str:
        """Ashby company ID."""
        val = os.environ.get("ASHBY_COMPANY_ID") or self.get(
            "scrapers.ashby.company_id", ""
        )
        return str(val)

    @property
    def ashby_enabled(self) -> bool:
        """Check if Ashby scraper is enabled."""
        val = os.environ.get("ASHBY_ENABLED") or self.get(
            "scrapers.ashby.enabled", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def smartrecruiters_company_id(self) -> str:
        """SmartRecruiters company ID."""
        val = os.environ.get("SMARTRECRUITERS_COMPANY_ID") or self.get(
            "scrapers.smartrecruiters.company_id", ""
        )
        return str(val)

    @property
    def smartrecruiters_enabled(self) -> bool:
        """Check if SmartRecruiters scraper is enabled."""
        val = os.environ.get("SMARTRECRUITERS_ENABLED") or self.get(
            "scrapers.smartrecruiters.enabled", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def icims_company_id(self) -> str:
        """iCIMS company ID."""
        val = os.environ.get("ICIMS_COMPANY_ID") or self.get(
            "scrapers.icims.company_id", ""
        )
        return str(val)

    @property
    def icims_enabled(self) -> bool:
        """Check if iCIMS scraper is enabled."""
        val = os.environ.get("ICIMS_ENABLED") or self.get(
            "scrapers.icims.enabled", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def oracle_company_id(self) -> str:
        """Oracle company ID."""
        val = os.environ.get("ORACLE_COMPANY_ID") or self.get(
            "scrapers.oracle.company_id", ""
        )
        return str(val)

    @property
    def oracle_enabled(self) -> bool:
        """Check if Oracle scraper is enabled."""
        val = os.environ.get("ORACLE_ENABLED") or self.get(
            "scrapers.oracle.enabled", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def successfactors_company_id(self) -> str:
        """SuccessFactors company ID."""
        val = os.environ.get("SUCCESSFACTORS_COMPANY_ID") or self.get(
            "scrapers.successfactors.company_id", ""
        )
        return str(val)

    @property
    def successfactors_enabled(self) -> bool:
        """Check if SuccessFactors scraper is enabled."""
        val = os.environ.get("SUCCESSFACTORS_ENABLED") or self.get(
            "scrapers.successfactors.enabled", False
        )
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    API_PREFIX: str = "/api/v1"
    API_VERSION: str = "1.0.0"

    @property
    def api_host(self) -> str:
        """API server host."""
        val = os.environ.get("API_HOST") or self.get("api.host", "127.0.0.1")
        return str(val)

    @property
    def api_port(self) -> int:
        """API server port."""
        val = os.environ.get("API_PORT") or self.get("api.port", 8000)
        try:
            return int(val)
        except (ValueError, TypeError):
            return 8000

    @property
    def api_debug(self) -> bool:
        """Check if API debug mode is enabled."""
        val = os.environ.get("API_DEBUG") or self.get("api.debug", False)
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    @property
    def jwt_secret_key(self) -> str:
        """JWT secret key."""
        val = os.environ.get("JWT_SECRET_KEY") or self.get("security.jwt_secret_key")
        if not val or val == "supersecretkey" or len(str(val)) < 32:
            from app.core.exceptions import ConfigurationError

            raise ConfigurationError(
                "JWT_SECRET_KEY is insecure, missing, or less than 32 characters."
            )
        return str(val)

    @property
    def jwt_algorithm(self) -> str:
        """JWT signature algorithm."""
        val = os.environ.get("JWT_ALGORITHM") or self.get(
            "security.jwt_algorithm", "HS256"
        )
        return str(val)

    @property
    def jwt_issuer(self) -> str:
        """JWT issuer identifier."""
        val = os.environ.get("JWT_ISSUER") or self.get(
            "security.jwt_issuer", "intern-intel"
        )
        return str(val)

    @property
    def jwt_audience(self) -> str:
        """JWT audience identifier."""
        val = os.environ.get("JWT_AUDIENCE") or self.get(
            "security.jwt_audience", "intern-intel-users"
        )
        return str(val)

    @property
    def access_token_expire_minutes(self) -> int:
        """Access token expiry in minutes."""
        val = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES") or self.get(
            "security.access_token_expire_minutes", 30
        )
        try:
            return int(val)
        except (ValueError, TypeError):
            return 30

    @property
    def refresh_token_expire_days(self) -> int:
        """Refresh token expiry in days."""
        val = os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS") or self.get(
            "security.refresh_token_expire_days", 7
        )
        try:
            return int(val)
        except (ValueError, TypeError):
            return 7

    @property
    def password_min_length(self) -> int:
        """Minimum password length rule."""
        val = os.environ.get("PASSWORD_MIN_LENGTH") or self.get(
            "security.password_min_length", 8
        )
        try:
            return int(val)
        except (ValueError, TypeError):
            return 8

    @property
    def password_max_length(self) -> int:
        """Maximum password length rule."""
        val = os.environ.get("PASSWORD_MAX_LENGTH") or self.get(
            "security.password_max_length", 128
        )
        try:
            return int(val)
        except (ValueError, TypeError):
            return 128
