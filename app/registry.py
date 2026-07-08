"""Registry for managing scraper construction factories by name."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from app.core.logger import logger
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.scrapers.workday import WorkdayScraper
from app.scrapers.ashby import AshbyScraper
from app.scrapers.smartrecruiters import SmartRecruitersScraper
from app.scrapers.icims import IcimsScraper
from app.scrapers.oracle import OracleScraper
from app.scrapers.successfactors import SuccessFactorsScraper

if TYPE_CHECKING:
    from app.core.base_scraper import BaseScraper
    from app.core.http_client import HttpClient
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


# Mapping of scraper name to factory function constructing the scraper.
# Adding a new ATS scraper only requires adding its builder function here.
SCRAPER_FACTORIES: dict[str, Callable[[HttpClient, Settings], BaseScraper]] = {
    "greenhouse": lambda hc, s: GreenhouseScraper(
        http_client=hc,
        board_token=s.greenhouse_board_token,
    ),
    "lever": lambda hc, s: LeverScraper(
        http_client=hc,
        site_slug=s.lever_site_slug,
    ),
    "workday": lambda hc, s: WorkdayScraper(
        http_client=hc,
        tenant=s.workday_tenant,
        parent_site_id=s.workday_parent_site_id,
    ),
    "ashby": lambda hc, s: AshbyScraper(
        http_client=hc,
        company_id=s.ashby_company_id,
    ),
    "smartrecruiters": lambda hc, s: SmartRecruitersScraper(
        http_client=hc,
        company_id=s.smartrecruiters_company_id,
    ),
    "icims": lambda hc, s: IcimsScraper(
        http_client=hc,
        company_id=s.icims_company_id,
    ),
    "oracle": lambda hc, s: OracleScraper(
        http_client=hc,
        company_id=s.oracle_company_id,
    ),
    "successfactors": lambda hc, s: SuccessFactorsScraper(
        http_client=hc,
        company_id=s.successfactors_company_id,
    ),
}


def create_default_registry(settings: Settings | None = None) -> CompanyRegistry:
    """Create a registry instance preconfigured with enabled scrapers.

    Args:
        settings: Optional custom Settings container.

    Returns:
        CompanyRegistry with default scraper factories registered.
    """
    from app.core.config import settings as default_settings
    from app.core.http_client import http_client

    active_settings = settings or default_settings
    registry = CompanyRegistry()

    for name, factory in SCRAPER_FACTORIES.items():
        enabled_flag = getattr(active_settings, f"{name}_enabled", False)
        if enabled_flag:
            # Closing over the specific loop variables
            def make_builder(f=factory):
                return lambda: f(http_client, active_settings)

            registry.register(name, make_builder())

    return registry
