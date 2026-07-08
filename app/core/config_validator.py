"""Configuration validation checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.exceptions import ConfigurationError

if TYPE_CHECKING:
    from app.core.settings import Settings

__all__ = ["ConfigValidator", "ValidationResult"]


@dataclass(frozen=True)
class ValidationResult:
    """Structure encapsulating config validation status and messages."""

    is_valid: bool
    errors: list[str]


class ConfigValidator:
    """Validator responsible for verifying configuration parameters correctness."""

    def validate(self, settings: Settings) -> ValidationResult:
        """Validate settings and return structured check results.

        Args:
            settings: Settings container instance to validate.

        Returns:
            ValidationResult containing status and errors list.
        """
        errors: list[str] = []

        # Validate Database URL format
        db_url = settings.database_url
        if not db_url or not db_url.strip():
            errors.append("Database URL must not be empty.")
        elif "://" not in db_url:
            errors.append(
                f"Database URL must specify driver schema (e.g. sqlite:///): '{db_url}'"
            )

        # Validate Telegram settings if enabled
        if settings.telegram_enabled:
            bot_token = settings.telegram_bot_token
            if not bot_token or not bot_token.strip():
                errors.append(
                    "Telegram bot token is required when notifications are enabled."
                )

            chat_id = settings.telegram_chat_id
            if not chat_id or not chat_id.strip():
                errors.append(
                    "Telegram chat ID is required when notifications are enabled."
                )

        # Validate Scheduler Interval
        try:
            interval = settings.scheduler_interval_seconds
            if interval <= 0:
                errors.append(
                    f"Scheduler interval must be positive integer, got: {interval}"
                )
        except (ValueError, TypeError) as exc:
            errors.append(f"Scheduler interval is invalid: {exc}")

        # Validate Scrapers configuration
        try:
            timeout = settings.scraper_timeout
            if timeout <= 0:
                errors.append(
                    f"Scraper timeout must be positive integer, got: {timeout}"
                )
        except (ValueError, TypeError) as exc:
            errors.append(f"Scraper timeout is invalid: {exc}")

        ua = settings.scraper_user_agent
        if not ua or not ua.strip():
            errors.append("Scraper User-Agent must not be empty.")

        if settings.greenhouse_enabled:
            greenhouse = settings.greenhouse_board_token
            if not greenhouse or not greenhouse.strip():
                errors.append("Greenhouse board token must not be empty.")

        if settings.lever_enabled:
            lever = settings.lever_site_slug
            if not lever or not lever.strip():
                errors.append("Lever site slug must not be empty.")

        if settings.workday_enabled:
            tenant = settings.workday_tenant
            site_id = settings.workday_parent_site_id
            if not tenant or not tenant.strip():
                errors.append("Workday tenant must not be empty.")
            if not site_id or not site_id.strip():
                errors.append("Workday parent site ID must not be empty.")

        if settings.ashby_enabled:
            company_id = settings.ashby_company_id
            if not company_id or not company_id.strip():
                errors.append("Ashby company ID must not be empty.")

        if settings.smartrecruiters_enabled:
            company_id = settings.smartrecruiters_company_id
            if not company_id or not company_id.strip():
                errors.append("SmartRecruiters company ID must not be empty.")

        if settings.icims_enabled:
            company_id = settings.icims_company_id
            if not company_id or not company_id.strip():
                errors.append("iCIMS company ID must not be empty.")

        if settings.oracle_enabled:
            company_id = settings.oracle_company_id
            if not company_id or not company_id.strip():
                errors.append("Oracle company ID must not be empty.")

        if settings.successfactors_enabled:
            company_id = settings.successfactors_company_id
            if not company_id or not company_id.strip():
                errors.append("SuccessFactors company ID must not be empty.")

        # Validate API configuration
        api_host = settings.api_host
        if not api_host or not api_host.strip():
            errors.append("API host must not be empty.")

        try:
            api_port = settings.api_port
            if not (1 <= api_port <= 65535):
                errors.append(f"API port must be between 1 and 65535, got: {api_port}")
        except (ValueError, TypeError) as exc:
            errors.append(f"API port is invalid: {exc}")

        return ValidationResult(is_valid=(len(errors) == 0), errors=errors)

    def validate_or_raise(self, settings: Settings) -> None:
        """Perform validation and raise ConfigurationError if invalid.

        Args:
            settings: Settings container instance.

        Raises:
            ConfigurationError: If any configuration validations fail.
        """
        result = self.validate(settings)
        if not result.is_valid:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(result.errors)}"
            )
