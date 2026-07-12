"""Startup configuration check and service initialization."""

from __future__ import annotations

from app.core.config_validator import ConfigValidator
from app.core.logger import logger
from app.core.settings import Settings
from app.registry import CompanyRegistry, create_default_registry

__all__ = ["Startup"]


class Startup:
    """Orchestrates initialization validation checks at startup."""

    def __init__(
        self,
        settings: Settings | None = None,
        validator: ConfigValidator | None = None,
    ) -> None:
        """Initialize the Startup runner.

        Args:
            settings: Settings container instance.
            validator: Validator logic instance.
        """
        self._settings = settings or Settings()
        self._validator = validator or ConfigValidator()

    def run(self) -> CompanyRegistry:
        """Validate settings configuration, log summaries, and return registry.

        Returns:
            Preconfigured CompanyRegistry instance.

        Raises:
            ConfigurationError: If validation checks fail.
        """
        logger.info("Initializing application startup validation sequence.")

        # 1. Validate configuration
        self._validator.validate_or_raise(self._settings)

        # 2. Database schema validation
        from app.database.migrations import MigrationService

        migration_service = MigrationService(settings=self._settings)
        try:
            if not migration_service.is_up_to_date():
                if self._settings.database_auto_upgrade:
                    logger.warning(
                        "Database schema is outdated. Auto-upgrade is enabled. Upgrading now..."
                    )
                    migration_service.upgrade()
                else:
                    logger.warning(
                        "Database schema is behind the latest migration. "
                        "Please run 'internintel db upgrade' to apply pending migrations."
                    )
            else:
                logger.info("Database schema is up to date.")
        except Exception as exc:
            logger.error("Failed to verify or upgrade database schema: {}", exc)
            raise

        # 3. Log startup summary details
        logger.info("Configuration checks completed successfully.")
        logger.info("--------------------------------------------------")
        logger.info("Database URL: {}", self._settings.database_url)
        logger.info(
            "Database Auto-Upgrade: {}",
            "ENABLED" if self._settings.database_auto_upgrade else "DISABLED",
        )
        logger.info(
            "Scheduler Interval: {} seconds", self._settings.scheduler_interval_seconds
        )
        logger.info("Logging level threshold: {}", self._settings.logging_level)
        logger.info(
            "Telegram notification status: {}",
            "ENABLED" if self._settings.telegram_enabled else "DISABLED",
        )
        logger.info("--------------------------------------------------")

        # 4. Initialize and return registry
        registry = create_default_registry(settings=self._settings)

        # 5. Provision default administrator account if it doesn't exist
        from app.database.session import get_session
        from app.database.user_repository import UserRepository
        from app.services.auth_service import AuthenticationService
        from app.models.user import UserRole

        try:
            with get_session() as session:
                user_repo = UserRepository(session)
                if not user_repo.get_by_username(
                    "admin"
                ) and not user_repo.get_by_email("admin@internintel.local"):
                    auth_service = AuthenticationService(self._settings)
                    auth_service.register(
                        username="admin",
                        email="admin@internintel.local",
                        password="Admin@12345",
                        role=UserRole.ADMIN,
                    )
                    logger.info(
                        "Default administrator account successfully provisioned."
                    )
                else:
                    logger.debug(
                        "Administrator account already exists. Skipping provisioning."
                    )
        except Exception as exc:
            logger.error("Failed to provision default administrator account: {}", exc)

        return registry
