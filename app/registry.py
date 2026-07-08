"""Registry for managing scraper construction factories by name."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from app.core.logger import logger

if TYPE_CHECKING:
    from app.core.base_scraper import BaseScraper
    from app.core.settings import Settings

__all__ = ["CompanyRegistry", "create_default_registry"]


class CompanyRegistry:
    """Registry responsible for managing scraper construction factories."""

    def __init__(self) -> None:
        """Initialize the CompanyRegistry."""
        self._factories: dict[str, Callable[[], BaseScraper]] = {}

    def register(self, name: str, factory: Callable[[], BaseScraper]) -> None:
        """Register a scraper factory by name.

        Args:
            name: Unique name of the scraper/company.
            factory: Callable constructing the scraper instance.

        Raises:
            ValueError: If name is empty, or scraper is already registered.
        """
        name = name.strip()
        if not name:
            raise ValueError("Scraper name must not be empty.")

        if name in self._factories:
            raise ValueError(f"Scraper already registered: {name}")

        self._factories[name] = factory
        logger.info("Registered scraper factory for name: '{}'", name)

    def get(self, name: str) -> Callable[[], BaseScraper]:
        """Retrieve a registered factory by name.

        Args:
            name: Registered name of the scraper.

        Returns:
            The scraper factory callable.

        Raises:
            ValueError: If name is not registered.
        """
        if name not in self._factories:
            raise ValueError(f"Scraper not registered: {name}")
        return self._factories[name]

    def create(self, name: str) -> BaseScraper:
        """Create a scraper instance by name.

        Args:
            name: Registered name of the scraper.

        Returns:
            Constructed BaseScraper instance.
        """
        factory = self.get(name)
        return factory()

    def create_all(self) -> list[BaseScraper]:
        """Construct instances of all registered scrapers.

        Returns:
            List of constructed scraper instances.
        """
        return [factory() for factory in self._factories.values()]

    def list_names(self) -> list[str]:
        """List names of all registered scrapers, preserving registration order.

        Returns:
            List of registered scraper names.
        """
        return list(self._factories.keys())

    def exists(self, name: str) -> bool:
        """Check whether a scraper name is registered.

        Args:
            name: Scraper name to verify.

        Returns:
            True if registered.
        """
        return name in self._factories

    def clear(self) -> None:
        """Clear all registered factories from the registry."""
        self._factories.clear()
        logger.info("Cleared all registered scraper factories.")


def create_default_registry(settings: Settings | None = None) -> CompanyRegistry:
    """Create a registry instance preconfigured with Greenhouse and Lever scrapers.

    Args:
        settings: Optional custom Settings container.

    Returns:
        CompanyRegistry with default scraper factories registered.
    """
    from app.core.config import settings as default_settings
    from app.core.http_client import http_client
    from app.scrapers.greenhouse import GreenhouseScraper
    from app.scrapers.lever import LeverScraper

    active_settings = settings or default_settings
    registry = CompanyRegistry()

    registry.register(
        "greenhouse",
        lambda: GreenhouseScraper(
            http_client=http_client,
            board_token=active_settings.greenhouse_board_token,
        ),
    )

    registry.register(
        "lever",
        lambda: LeverScraper(
            http_client=http_client,
            site_slug=active_settings.lever_site_slug,
        ),
    )

    return registry
