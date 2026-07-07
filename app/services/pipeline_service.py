"""Pipeline service for orchestrating scraping, deduplication, mapping, and persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import settings
from app.core.exceptions import DatabaseError, InternIntelError, ScraperError
from app.core.http_client import http_client
from app.core.logger import logger
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.services.database_service import DatabaseService
from app.services.dedup_service import DedupService
from app.services.mapper_service import MapperService
from app.services.scraper_service import ScraperService

if TYPE_CHECKING:
    from app.core.base_scraper import BaseScraper
    from app.models.internship import Internship

__all__ = [
    "MapperError",
    "PipelineService",
]


class MapperError(InternIntelError):
    """Raised when mapping normalized job dictionaries fails."""


class PipelineService:
    """Coordinate the complete internship processing pipeline.

    Pipeline stages:

    1. Scrape internship listings.
    2. Remove duplicate listings.
    3. Map dictionaries to ORM models.
    4. Persist models into the database.
    """

    def __init__(
        self,
        scraper_service: ScraperService | None = None,
        dedup_service: DedupService | None = None,
        mapper_service: MapperService | None = None,
        database_service: DatabaseService | None = None,
    ) -> None:
        """Initialize pipeline dependencies.

        Args:
            scraper_service: Scraping service.
            dedup_service: Deduplication service.
            mapper_service: Mapping service.
            database_service: Database persistence service.
        """
        self._scraper_service = scraper_service or ScraperService(http_client)
        self._dedup_service = dedup_service or DedupService()
        self._mapper_service = mapper_service or MapperService()
        self._database_service = database_service or DatabaseService()

    def _create_default_scrapers(self) -> list[BaseScraper]:
        """Create the configured default scraper instances."""

        greenhouse_token = settings.get(
            "scrapers.greenhouse.board_token",
            "google",
        )

        lever_slug = settings.get(
            "scrapers.lever.site_slug",
            "veriff",
        )

        return [
            GreenhouseScraper(
                http_client=http_client,
                board_token=greenhouse_token,
            ),
            LeverScraper(
                http_client=http_client,
                site_slug=lever_slug,
            ),
        ]

    def run(self) -> list[Internship]:
        """Run the pipeline using configured default scrapers.

        Returns:
            Saved Internship ORM models.
        """
        return self.run_scrapers(
            self._create_default_scrapers(),
        )

    def run_scrapers(
        self,
        scrapers: list[BaseScraper],
    ) -> list[Internship]:
        """Execute the pipeline with custom scraper instances.

        Args:
            scrapers: Scrapers to execute.

        Returns:
            Saved Internship ORM models.

        Raises:
            ScraperError:
                If scraping fails.

            MapperError:
                If mapping fails.

            DatabaseError:
                If database persistence fails.
        """
        logger.info("Pipeline started.")

        try:
            raw_jobs = self._scraper_service.scrape_many(scrapers)
            logger.info(
                "Fetched {} raw jobs.",
                len(raw_jobs),
            )

            if not raw_jobs:
                logger.info(
                    "Pipeline finished. No jobs were scraped.",
                )
                return []

            unique_jobs = self._dedup_service.deduplicate(raw_jobs)
            logger.info(
                "{} unique jobs after deduplication.",
                len(unique_jobs),
            )

            if not unique_jobs:
                logger.info(
                    "Pipeline finished. No unique jobs found.",
                )
                return []

            mapped_jobs = self._mapper_service.map_many(unique_jobs)
            logger.info(
                "Mapped {} internship objects.",
                len(mapped_jobs),
            )

            if not mapped_jobs:
                logger.info(
                    "Pipeline finished. Nothing to save.",
                )
                return []

            saved_jobs = self._database_service.save_many(mapped_jobs)

            logger.info(
                "Saved {} internship listings.",
                len(saved_jobs),
            )

            logger.info(
                "Pipeline completed successfully.",
            )

            return saved_jobs

        except (ScraperError, MapperError, DatabaseError) as exc:
            logger.exception(
                "Pipeline execution failed: {}",
                exc,
            )
            raise
