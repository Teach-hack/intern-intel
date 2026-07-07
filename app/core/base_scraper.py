"""Base scraper abstraction for the InternIntel application.

This module defines the abstract base class and common lifecycle interface
reused by all company scrapers and ATS connectors in the application.
"""

from __future__ import annotations

import abc
import time
from typing import Any

from app.core.exceptions import (
    ScraperBlockedError,
    ScraperError,
    ScraperParsingError,
)
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["BaseScraper"]

# Module-level constants for status codes and validation fields
_BLOCKED_STATUS_CODES: frozenset[int] = frozenset({403, 429})
_REQUIRED_VALIDATION_FIELDS: tuple[str, ...] = (
    "company",
    "title",
    "url",
    "employment_type",
    "work_mode",
    "source",
    "status",
)


class BaseScraper(abc.ABC):
    """Abstract base class for all internship scrapers.

    Orchestrates the scraping lifecycle: fetching page content, parsing
    raw listings, normalizing them into the canonical schema, validating
    required fields, and logging statistics.

    Uses dependency injection for its HttpClient.
    """

    def __init__(self, http_client: HttpClient, source_url: str | None = None) -> None:
        """Initialize the base scraper.

        Args:
            http_client: Centralized HTTP client instance.
            source_url: Default URL to scrape for this source.
        """
        self._http_client = http_client
        self._source_url = source_url

    def scrape(self, url: str | None = None) -> list[dict[str, Any]]:
        """Orchestrate the complete scraping lifecycle for the given URL.

        Executes: fetch -> parse -> normalize -> validate -> log.

        Args:
            url: URL to fetch page content from. If not provided, falls back
                to the default source_url configured at initialization.

        Returns:
            A list of normalized, validated internship dicts.

        Raises:
            ScraperError: On general scraping or network failure.
            ScraperBlockedError: If the request is blocked (403, 429).
            ScraperParsingError: If page parsing fails.
        """
        target_url = url or self._source_url
        if not target_url:
            raise ScraperError("No scraping URL provided and no default URL configured")

        source_name = self.get_source_name()
        logger.debug(
            "Starting scrape workflow for source: {} URL: {}", source_name, target_url
        )

        start_time = time.monotonic()
        content = self.fetch_page(target_url)
        raw_listings = self.parse_listings(content)

        logger.debug(
            "Parsed {} raw listings from source: {}", len(raw_listings), source_name
        )

        validated_listings: list[dict[str, Any]] = []
        rejected_count = 0
        failed_normalize_count = 0

        for raw in raw_listings:
            try:
                normalized = self.normalize(raw)
            except ScraperParsingError as exc:
                logger.warning(
                    "Normalization failed for raw listing in source {}: {}",
                    source_name,
                    exc,
                )
                failed_normalize_count += 1
                continue
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                logger.warning(
                    "Unexpected parsing error during normalization in source {}: {}",
                    source_name,
                    exc,
                )
                failed_normalize_count += 1
                continue

            if self.validate(normalized):
                validated_listings.append(normalized)
            else:
                rejected_count += 1

        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "Scrape complete for source: {} URL: {} | Parsed: {} | Validated: {} | "
            "Rejected: {} | Failed Normalize: {} | Duration: {:.0f}ms",
            source_name,
            target_url,
            len(raw_listings),
            len(validated_listings),
            rejected_count,
            failed_normalize_count,
            elapsed_ms,
        )

        return validated_listings

    def fetch_page(self, url: str) -> str:
        """Fetch the page content for a given URL via the injected HTTP Client.

        Args:
            url: The target URL to fetch.

        Returns:
            The raw text content of the response.

        Raises:
            ScraperBlockedError: If the remote site returns 403 or 429.
            HttpClientError: Propagated directly from the HTTP Client.
        """
        source_name = self.get_source_name()
        response = self._http_client.get(url)
        if response.status_code in _BLOCKED_STATUS_CODES:
            logger.error(
                "Blocked by target site for source: {} URL: {} Status: {}",
                source_name,
                url,
                response.status_code,
            )
            raise ScraperBlockedError(
                f"Access blocked with status code {response.status_code}"
            )
        return response.text

    @abc.abstractmethod
    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw listings from page content.

        Args:
            content: The raw HTML or JSON content of the response page.

        Returns:
            A list of raw dictionary objects. Each dictionary represents
            an individual listing item found on the source page.

        Raises:
            ScraperParsingError: If parse validation fails or no elements found.
        """

    @abc.abstractmethod
    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize field names and formats of a raw listing to the canonical schema.

        Args:
            raw: Raw dictionary representation of a single scraped listing.

        Returns:
            A dict conforming to the canonical Internship schema fields.

        Raises:
            ScraperParsingError: If raw structure is malformed or conversion fails.
        """

    @abc.abstractmethod
    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, e.g. "greenhouse".
        """

    def validate(self, listing: dict[str, Any]) -> bool:
        """Validate that a normalized listing contains all required fields and is non-empty.

        Args:
            listing: A normalized dictionary conforming to the Internship schema.

        Returns:
            True if the listing is valid, False otherwise.
        """
        source_name = self.get_source_name()

        for field in _REQUIRED_VALIDATION_FIELDS:
            if field not in listing:
                logger.warning(
                    "[{}] Validation failed: missing required field '{}' (title: {}, url: {})",
                    source_name,
                    field,
                    listing.get("title", "<unknown>"),
                    listing.get("url", "<unknown>"),
                )
                return False
            val = listing[field]
            if not isinstance(val, str) or not val.strip():
                logger.warning(
                    "[{}] Validation failed: required field '{}' is empty or not a string "
                    "(title: {}, url: {})",
                    source_name,
                    field,
                    listing.get("title", "<unknown>"),
                    listing.get("url", "<unknown>"),
                )
                return False

        return True

    def close(self) -> None:
        """Clean up subclass-specific resources.

        Safe to call multiple times. The Base Scraper does not own the
        HttpClient and must not close it.
        """
