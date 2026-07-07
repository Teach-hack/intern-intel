"""Service for orchestrating and running multiple scrapers."""

from __future__ import annotations

from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperError
from app.core.logger import logger

__all__ = ["ScraperService"]


class ScraperService:
    """Service to orchestrate and run BaseScraper implementations.

    Manages running scrapers individually or in bulk, consolidating results,
    and handling failures gracefully.
    """

    def __init__(self) -> None:
        """Initialize the ScraperService."""
        pass

    def scrape(self, scraper: BaseScraper) -> list[dict[str, Any]]:
        """Run a single scraper and return its normalized listings.

        Args:
            scraper: The scraper instance to execute.

        Returns:
            A list of normalized internship listings.

        Raises:
            ScraperError: Propagated if scraper execution fails.
        """
        source = scraper.get_source_name()

        logger.info("Starting scraper run for source: {}", source)

        try:
            listings = scraper.scrape()

            logger.info(
                "Finished scraper run for source: {} | Found {} listings",
                source,
                len(listings),
            )

            return listings

        except ScraperError as exc:
            logger.error(
                "Scraper run failed for source {}: {}",
                source,
                exc,
            )
            raise

    def scrape_many(self, scrapers: list[BaseScraper]) -> list[dict[str, Any]]:
        """Run multiple scrapers sequentially and combine their results.

        If an individual scraper fails, the failure is logged and execution
        continues with the remaining scrapers.

        Args:
            scrapers: List of scraper instances to execute.

        Returns:
            Combined list of normalized internship listings.
        """
        combined_listings: list[dict[str, Any]] = []

        for scraper in scrapers:
            try:
                combined_listings.extend(self.scrape(scraper))
            except ScraperError:
                # Error already logged by scrape().
                continue

        return combined_listings
