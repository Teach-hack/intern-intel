"""Unit tests for the ScraperService."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperError
from app.core.http_client import HttpClient
from app.services.scraper_service import ScraperService


class _MockScraper(BaseScraper):
    """Concrete mock implementation of BaseScraper for testing."""

    def __init__(
        self,
        http_client: HttpClient,
        source: str = "mock_source",
        listings: list[dict[str, Any]] | None = None,
        should_fail: bool = False,
        non_scraper_error: bool = False,
    ) -> None:
        super().__init__(http_client, source_url="https://example.com")
        self.source = source
        self.listings = listings or []
        self.should_fail = should_fail
        self.non_scraper_error = non_scraper_error

    def get_source_name(self) -> str:
        return self.source

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        return []

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {}

    def scrape(self, url: str | None = None) -> list[dict[str, Any]]:
        if self.should_fail:
            raise ScraperError(f"Scraper {self.source} failed purposefully")

        if self.non_scraper_error:
            raise ValueError("Unexpected system failure")

        return self.listings


def test_scraper_service_initialization() -> None:
    """Verify that ScraperService initializes correctly."""
    service = ScraperService()
    assert isinstance(service, ScraperService)


def test_scrape_success() -> None:
    """Verify that scrape successfully runs a single scraper and logs start/end."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService()

    expected_listings = [{"title": "Intern", "company": "A"}]

    scraper = _MockScraper(
        mock_client,
        source="source_a",
        listings=expected_listings,
    )

    with patch("app.services.scraper_service.logger") as mock_logger:
        results = service.scrape(scraper)

        assert results == expected_listings
        assert mock_logger.info.call_count == 2

        start_args = mock_logger.info.call_args_list[0][0]
        assert "Starting scraper run for source: {}" in start_args[0]
        assert start_args[1] == "source_a"

        end_args = mock_logger.info.call_args_list[1][0]
        assert "Finished scraper run for source: {} | Found {} listings" in end_args[0]
        assert end_args[1] == "source_a"
        assert end_args[2] == 1


def test_scrape_failure() -> None:
    """Verify that scrape logs error and re-raises ScraperError."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService()

    scraper = _MockScraper(
        mock_client,
        source="source_fail",
        should_fail=True,
    )

    with patch("app.services.scraper_service.logger") as mock_logger:
        with pytest.raises(ScraperError, match="failed purposefully"):
            service.scrape(scraper)

        mock_logger.error.assert_called_once()

        error_args = mock_logger.error.call_args[0]
        assert "Scraper run failed for source {}: {}" in error_args[0]
        assert error_args[1] == "source_fail"


def test_scrape_non_scraper_error_propagation() -> None:
    """Verify that non-ScraperError exceptions propagate."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService()

    scraper = _MockScraper(
        mock_client,
        source="source_non_scraper_fail",
        non_scraper_error=True,
    )

    with pytest.raises(ValueError, match="Unexpected system failure"):
        service.scrape(scraper)


def test_scrape_many_success() -> None:
    """Verify that scrape_many combines results from successful scrapers."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService()

    scraper_a = _MockScraper(
        mock_client,
        source="source_a",
        listings=[{"title": "Job A"}],
    )

    scraper_b = _MockScraper(
        mock_client,
        source="source_b",
        listings=[{"title": "Job B"}],
    )

    results = service.scrape_many([scraper_a, scraper_b])

    assert len(results) == 2
    assert results[0]["title"] == "Job A"
    assert results[1]["title"] == "Job B"


def test_scrape_many_partial_failure() -> None:
    """Verify that scrape_many continues after a ScraperError."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService()

    scraper_a = _MockScraper(
        mock_client,
        source="source_a",
        listings=[{"title": "Job A"}],
    )

    scraper_fail = _MockScraper(
        mock_client,
        source="source_fail",
        should_fail=True,
    )

    scraper_b = _MockScraper(
        mock_client,
        source="source_b",
        listings=[{"title": "Job B"}],
    )

    results = service.scrape_many([scraper_a, scraper_fail, scraper_b])

    assert len(results) == 2
    assert results[0]["title"] == "Job A"
    assert results[1]["title"] == "Job B"


def test_scrape_many_non_scraper_error_propagation() -> None:
    """Verify that unexpected exceptions propagate."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService()

    scraper_a = _MockScraper(
        mock_client,
        source="source_a",
        listings=[{"title": "Job A"}],
    )

    scraper_non_scraper_fail = _MockScraper(
        mock_client,
        source="source_non_scraper_fail",
        non_scraper_error=True,
    )

    scraper_b = _MockScraper(
        mock_client,
        source="source_b",
        listings=[{"title": "Job B"}],
    )

    with pytest.raises(ValueError, match="Unexpected system failure"):
        service.scrape_many(
            [
                scraper_a,
                scraper_non_scraper_fail,
                scraper_b,
            ]
        )
