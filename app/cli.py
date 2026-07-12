"""Command Line Interface for InternIntel."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import Any

from app.core import Settings, Startup
from app.core.config import settings as settings  # noqa: F401  # accessed via globals()
from app.core.logger import logger
from app.notifications.message_builder import MessageBuilder
from app.notifications.notification_service import NotificationService
from app.notifications.telegram import TelegramNotifier
from app.runner import Runner
from app.scheduler import Scheduler
from app.services.database_service import DatabaseService

__all__ = ["CLI", "main"]


class CLI:
    """Argparse-based CLI for driving InternIntel orchestrations."""

    def __init__(
        self,
        runner: Runner | None = None,
        database_service: DatabaseService | None = None,
        notification_service: NotificationService | None = None,
        settings: Settings | None = None,
        startup: Startup | None = None,
    ) -> None:
        """Initialize CLI with injected services.

        Args:
            runner: Injectable application Runner orchestration service.
            database_service: Injectable database operations service.
            notification_service: Injectable notification service.
            settings: Injectable settings container.
            startup: Injectable startup initialization.
        """
        self._custom_settings = settings
        self._startup = startup or Startup(settings=self._active_settings)

        self._runner = runner or Runner(settings=self._active_settings)
        self._database_service = database_service or DatabaseService()
        self._notification_service = notification_service

    @property
    def _active_settings(self) -> Settings:
        """Resolve current active settings instance dynamically."""
        if self._custom_settings is not None:
            return self._custom_settings
        return globals()["settings"]

    def _get_notification_service(self) -> NotificationService:
        """Lazily retrieve or build the notification service.

        Returns:
            NotificationService configured with token & chat ID.
        """
        if self._notification_service is not None:
            return self._notification_service

        active_settings = self._active_settings
        bot_token = active_settings.get("notification.telegram_bot_token")
        chat_id = active_settings.get("notification.telegram_chat_id")

        notifier = None
        if bot_token and chat_id:
            notifier = TelegramNotifier(bot_token=str(bot_token), chat_id=str(chat_id))

        return NotificationService(
            message_builder=MessageBuilder(),
            notifier=notifier,
        )

    def run(self) -> int:
        """Execute the full scraping pipeline and send notifications for new listings.

        Returns:
            Exit code.
        """
        logger.info("Executing CLI 'run' command.")
        self._startup.run()
        self._runner.run()
        return 0

    def scrape(self) -> int:
        """Execute the scraping pipeline but skip notification dispatches.

        Returns:
            Exit code.
        """
        logger.info("Executing CLI 'scrape' command.")
        self._startup.run()
        no_notify_service = NotificationService(notifier=None)
        runner = Runner(
            pipeline_service=self._runner._pipeline_service,
            notification_service=no_notify_service,
            settings=self._active_settings,
        )
        runner.run()
        return 0

    def notify(self) -> int:
        """Send notifications for all existing internship records in the database.

        Returns:
            Exit code.
        """
        logger.info("Executing CLI 'notify' command.")
        self._startup.run()
        jobs = self._database_service.get_all()
        if not jobs:
            logger.info("No internships found in database to notify.")
            return 0

        ns = self._get_notification_service()
        ns.notify_many(jobs)
        return 0

    def scheduler(self) -> int:
        """Start the periodic interval scheduler.

        Returns:
            Exit code.
        """
        logger.info("Executing CLI 'scheduler' command.")
        self._startup.run()
        active_settings = self._active_settings
        interval = active_settings.get("scheduler.interval_seconds", 3600)
        s = Scheduler(runner=self._runner, interval_seconds=interval)
        s.run_forever()
        return 0

    def version(self) -> int:
        """Print the current application version.

        Returns:
            Exit code.
        """
        ver = self._active_settings.get("app.version", "0.1.0")
        print(f"InternIntel v{ver}")
        return 0

    def doctor(self) -> int:
        """Run diagnostic validation checks on configuration and database path.

        Returns:
            0 if healthy, non-zero exit code if configuration contains errors.
        """
        logger.info("Executing CLI 'doctor' command.")
        active_settings = self._active_settings
        try:
            active_settings.reload()
            print("[OK] Configuration load successful.")
        except Exception as exc:
            print(f"[ERROR] Failed to load configuration: {exc}")
            return 1

        # Read all config values using .get() — works uniformly on both
        # real Settings and MagicMock objects used in tests.
        db_path = active_settings.get("database.path")
        db_url = active_settings.get("database.url")
        if not db_url and db_path:
            db_url = f"sqlite:///{db_path}"

        telegram_enabled = active_settings.get("notification.telegram", False)
        if isinstance(telegram_enabled, str):
            telegram_enabled = telegram_enabled.lower() in ("true", "1", "yes")
        else:
            telegram_enabled = bool(telegram_enabled)

        bot_token = active_settings.get("notification.telegram_bot_token")
        chat_id = active_settings.get("notification.telegram_chat_id")
        interval = active_settings.get("scheduler.interval_seconds", 3600)

        # Determine validity based on database path presence
        is_valid = db_path is not None
        errors: list[str] = [] if is_valid else ["Database path is missing."]

        print("\n--- Diagnostics ---")
        if is_valid:
            print("Status: HEALTHY")
        else:
            print("Status: UNHEALTHY")
            for error in errors:
                print(f" - [ERROR] {error}")

        # Database Status
        print(f"Database URL: {db_url}")
        if not db_path:
            print("[ERROR] Database path is not configured.")
        else:
            print(f"[OK] Database path configured: {db_path}")

        # Telegram Configuration Status
        print(
            f"Telegram Notifications: {'ENABLED' if telegram_enabled else 'DISABLED'}"
        )
        if telegram_enabled:
            if not bot_token or not chat_id:
                print("[WARN] Telegram enabled but token or chat ID is missing.")
            else:
                print("[OK] Telegram settings configured.")
            print(f" - Bot Token: {'Configured' if bot_token else 'MISSING'}")
            print(f" - Chat ID: {'Configured' if chat_id else 'MISSING'}")

        # Scheduler Interval
        print(f"Scheduler Interval: {interval}s")

        # Registered Scrapers
        from app.registry import create_default_registry, SCRAPER_FACTORIES
        from app.core.config_validator import ConfigValidator

        registry = create_default_registry(settings=active_settings)
        all_scrapers = list(SCRAPER_FACTORIES.keys())

        enabled_scrapers = []
        for name in all_scrapers:
            default_enabled = name in ("greenhouse", "lever")
            enabled_val = active_settings.get(f"scrapers.{name}.enabled")
            if enabled_val is None:
                try:
                    is_enabled = bool(
                        getattr(active_settings, f"{name}_enabled", default_enabled)
                    )
                except AttributeError:
                    is_enabled = default_enabled
            else:
                if isinstance(enabled_val, str):
                    is_enabled = enabled_val.lower() in ("true", "1", "yes")
                else:
                    is_enabled = bool(enabled_val)
            if is_enabled:
                enabled_scrapers.append(name)

        disabled_scrapers = [
            name for name in all_scrapers if name not in enabled_scrapers
        ]

        print(f"Registered Scrapers: {', '.join(registry.list_names())}")
        print(f"Enabled Scrapers: {', '.join(enabled_scrapers)}")
        print(f"Disabled Scrapers: {', '.join(disabled_scrapers)}")

        validator = ConfigValidator()
        res = validator.validate(active_settings)
        if not res.is_valid:
            print("[ERROR] Configuration validation errors found:")
            for error in res.errors:
                print(f" - {error}")
            is_valid = False

        return 0 if is_valid else 1

    def create_admin(self, username: str, email: str, password: str) -> int:
        """Create a new admin user directly from CLI.
        
        Args:
            username: Admin username.
            email: Admin email.
            password: Admin password.
            
        Returns:
            Exit code.
        """
        from app.services.auth_service import AuthenticationService
        from app.models.user import UserRole
        
        logger.info("Executing CLI 'create-admin' command.")
        self._startup.run()
        
        auth_service = AuthenticationService(self._active_settings)
        try:
            user = auth_service.register(
                username=username,
                email=email,
                password=password,
                role=UserRole.ADMIN
            )
            print(f"[OK] Admin user '{user.username}' created successfully.")
            return 0
        except Exception as exc:
            print(f"[ERROR] Failed to create admin: {exc}")
            return 1

    def serve(
        self,
        host: str | None = None,
        port: int | None = None,
        reload: bool = False,
    ) -> int:
        """Start the FastAPI REST API web server using Uvicorn.

        Args:
            host: IP address to bind.
            port: Port number to bind.
            reload: Enable auto-reload of code changes.

        Returns:
            Exit code.
        """
        import uvicorn

        logger.info("Executing CLI 'serve' command.")
        active_settings = self._active_settings

        # Fallback to configured defaults if not overridden in CLI args
        bind_host = host or active_settings.api_host
        bind_port = port or active_settings.api_port

        logger.info(
            "Starting API server on {}:{} (reload={})",
            bind_host,
            bind_port,
            reload,
        )
        uvicorn.run("app.api:app", host=bind_host, port=bind_port, reload=reload)
        return 0

    def _get_migration_service(self) -> Any:
        """Lazily retrieve MigrationService."""
        from app.database.migrations import MigrationService

        return MigrationService(settings=self._active_settings)

    def execute(self, args: Sequence[str] | None = None) -> int:
        """Parse arguments and route execution to sub-commands.

        Args:
            args: Option strings list to parse. Defaults to sys.argv[1:].

        Returns:
            Exit code.
        """
        parser = argparse.ArgumentParser(
            description="InternIntel orchestration runner."
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        # Top-level commands
        subparsers.add_parser(
            "run", help="Execute the full scraping pipeline and notify"
        )
        subparsers.add_parser(
            "scrape", help="Execute the scraping pipeline but skip notification"
        )
        subparsers.add_parser(
            "notify", help="Send notifications for all existing internship records"
        )
        subparsers.add_parser("scheduler", help="Start the periodic interval scheduler")
        subparsers.add_parser("version", help="Print the current application version")
        subparsers.add_parser("doctor", help="Run diagnostic validation checks")

        # create-admin command
        admin_parser = subparsers.add_parser("create-admin", help="Create an admin user")
        admin_parser.add_argument("--username", required=True, help="Admin username")
        admin_parser.add_argument("--email", required=True, help="Admin email")
        admin_parser.add_argument("--password", required=True, help="Admin password")

        # serve command
        serve_parser = subparsers.add_parser(
            "serve", help="Start the FastAPI REST API web server"
        )
        serve_parser.add_argument("--host", help="IP address to bind the server")
        serve_parser.add_argument("--port", type=int, help="Port to bind the server")
        serve_parser.add_argument(
            "--reload", action="store_true", help="Enable auto-reload on code change"
        )

        # DB commands
        db_parser = subparsers.add_parser("db", help="Database migration commands")
        db_subparsers = db_parser.add_subparsers(dest="db_command", required=True)

        # db upgrade
        upgrade_parser = db_subparsers.add_parser(
            "upgrade", help="Upgrade to a later revision"
        )
        upgrade_parser.add_argument(
            "revision", nargs="?", default="head", help="Revision identifier"
        )

        # db downgrade
        downgrade_parser = db_subparsers.add_parser(
            "downgrade", help="Revert to a previous revision"
        )
        downgrade_parser.add_argument("revision", help="Revision identifier")

        # db current
        db_subparsers.add_parser("current", help="Display the current revision")

        # db history
        db_subparsers.add_parser(
            "history", help="List changeset scripts in chronological order"
        )

        # db revision
        revision_parser = db_subparsers.add_parser(
            "revision", help="Create a new revision file"
        )
        revision_parser.add_argument(
            "-m",
            "--message",
            required=True,
            help="Message string to use with 'revision'",
        )
        revision_parser.add_argument(
            "--autogenerate",
            action="store_true",
            help="Populate revision script with candidate migration operations",
        )

        parsed_args = parser.parse_args(args)
        cmd = parsed_args.command

        if cmd == "run":
            return self.run()
        if cmd == "scrape":
            return self.scrape()
        if cmd == "notify":
            return self.notify()
        if cmd == "scheduler":
            return self.scheduler()
        if cmd == "version":
            return self.version()
        if cmd == "doctor":
            return self.doctor()
        if cmd == "create-admin":
            return self.create_admin(
                username=parsed_args.username,
                email=parsed_args.email,
                password=parsed_args.password,
            )
        if cmd == "serve":
            return self.serve(
                host=parsed_args.host,
                port=parsed_args.port,
                reload=parsed_args.reload,
            )

        if cmd == "db":
            ms = self._get_migration_service()
            db_cmd = parsed_args.db_command
            try:
                if db_cmd == "upgrade":
                    ms.upgrade(parsed_args.revision)
                elif db_cmd == "downgrade":
                    ms.downgrade(parsed_args.revision)
                elif db_cmd == "current":
                    ms.current()
                elif db_cmd == "history":
                    ms.history()
                elif db_cmd == "revision":
                    ms.revision(
                        message=parsed_args.message,
                        autogenerate=parsed_args.autogenerate,
                    )
                print(f"[OK] Database command '{db_cmd}' completed successfully.")
                return 0
            except Exception as exc:
                print(f"[ERROR] Database command '{db_cmd}' failed: {exc}")
                return 1

        return 1


def main(args: Sequence[str] | None = None) -> None:
    """CLI script execution entry point.

    Args:
        args: Sequence of command line arguments.
    """
    cli = CLI()
    try:
        sys.exit(cli.execute(args))
    except SystemExit:
        raise
    except Exception as exc:
        logger.exception("Fatal CLI execution error: {}", exc)
        sys.exit(1)
