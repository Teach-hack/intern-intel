"""Service wrapper for Alembic programmatic migrations."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.core.logger import logger
from app.core.settings import Settings

__all__ = ["MigrationService"]


class MigrationService:
    """Service wrapping Alembic programmatic migration API."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the MigrationService.

        Args:
            settings: Injectable application settings.
        """
        self._settings = settings or Settings()

        # Find the root project directory by looking up from this file's location
        project_root = Path(__file__).resolve().parent.parent.parent
        self._alembic_ini_path = project_root / "alembic.ini"
        self._alembic_script_loc = project_root / "alembic"

        if not self._alembic_ini_path.is_file():
            logger.warning(
                "alembic.ini not found at %s. Migrations may fail.",
                self._alembic_ini_path,
            )

        self._alembic_cfg = Config(str(self._alembic_ini_path))
        self._alembic_cfg.set_main_option(
            "script_location", str(self._alembic_script_loc)
        )
        self._alembic_cfg.set_main_option("sqlalchemy.url", self._settings.database_url)

    def is_up_to_date(self) -> bool:
        """Check if the database schema is up to date with the latest migration script.

        Returns:
            True if up to date, False otherwise.
        """
        script = ScriptDirectory.from_config(self._alembic_cfg)
        head_rev = script.get_current_head()

        # If there are no scripts, there's nothing to be up-to-date with.
        if head_rev is None:
            return True

        from sqlalchemy import create_engine

        local_engine = create_engine(self._settings.database_url)

        with local_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        local_engine.dispose()

        return current_rev == head_rev

    def upgrade(self, revision: str = "head") -> None:
        """Upgrade the database to a later revision.

        Args:
            revision: Target revision string. Defaults to "head".
        """
        logger.info("Upgrading database to revision '%s'", revision)
        command.upgrade(self._alembic_cfg, revision)
        logger.info("Database upgrade complete.")

    def downgrade(self, revision: str) -> None:
        """Downgrade the database to an earlier revision.

        Args:
            revision: Target revision string.
        """
        logger.info("Downgrading database to revision '%s'", revision)
        command.downgrade(self._alembic_cfg, revision)
        logger.info("Database downgrade complete.")

    def current(self) -> None:
        """Display the current revision of the database."""
        logger.info("Checking current database revision.")
        command.current(self._alembic_cfg, verbose=True)

    def history(self) -> None:
        """List the history of migrations."""
        logger.info("Fetching database migration history.")
        command.history(self._alembic_cfg, indicate_current=True)

    def revision(self, message: str, autogenerate: bool = False) -> None:
        """Create a new migration revision.

        Args:
            message: Migration message describing the changes.
            autogenerate: Whether to auto-detect schema changes.
        """
        logger.info(
            "Creating new revision: '%s' (autogenerate=%s)", message, autogenerate
        )
        command.revision(self._alembic_cfg, message=message, autogenerate=autogenerate)
        logger.info("New revision created successfully.")
