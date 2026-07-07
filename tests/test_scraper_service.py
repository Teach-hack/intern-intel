"""Unit tests for the ScraperService."""

from __future__ import annotations

from typing import Any, final
from unittest.mock import MagicMock, patch

import pytest

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperError
from app.core.http_client import HttpClient
from app.services.scraper_service import ScraperService


@final
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
        self.listings = listings if listings is not None else []
        self.should_fail = should_fail
        self.non_scraper_error = non_scraper_error
        self.scrape_calls = 0

    def get_source_name(self) -> str:
        return self.source

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        return []

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {}

    def scrape(self, url: str | None = None) -> list[dict[str, Any]]:
        self.scrape_calls += 1

        if self.should_fail:
            raise ScraperError(f"Scraper {self.source} failed purposefully")

        if self.non_scraper_error:
            raise ValueError("Unexpected system failure")

        return self.listings


def test_scraper_service_initialization() -> None:
    """Verify that ScraperService initializes correctly."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService(mock_client)

    assert isinstance(service, ScraperService)


def test_scrape_success() -> None:
    """Verify that scrape successfully runs a scraper."""
    mock_client = MagicMock(spec=HttpClient)

    scraper = _MockScraper(
        mock_client,
        source="source_a",
        listings=[{"title": "Intern", "company": "A"}],
    )

    service = ScraperService(mock_client)

    with patch("app.services.scraper_service.logger") as mock_logger:
        results = service.scrape(scraper)

    assert results == [{"title": "Intern", "company": "A"}]
    assert scraper.scrape_calls == 1

    assert mock_logger.info.call_count == 2

    start_args = mock_logger.info.call_args_list[0][0]
    assert start_args[1] == "source_a"

    end_args = mock_logger.info.call_args_list[1][0]
    assert end_args[1] == "source_a"
    assert end_args[2] == 1


def test_scrape_failure() -> None:
    """Verify that ScraperError is logged and re-raised."""
    mock_client = MagicMock(spec=HttpClient)

    scraper = _MockScraper(
        mock_client,
        source="source_fail",
        should_fail=True,
    )

    service = ScraperService(mock_client)

    with patch("app.services.scraper_service.logger") as mock_logger:
        with pytest.raises(ScraperError):
            service.scrape(scraper)

    mock_logger.error.assert_called_once()


def test_scrape_non_scraper_error_propagation() -> None:
    """Verify that unexpected exceptions propagate."""
    mock_client = MagicMock(spec=HttpClient)

    scraper = _MockScraper(
        mock_client,
        non_scraper_error=True,
    )

    service = ScraperService(mock_client)

    with pytest.raises(ValueError):
        service.scrape(scraper)


def test_scrape_many_success() -> None:
    """Verify multiple successful scrapers are combined."""
    mock_client = MagicMock(spec=HttpClient)

    scraper_a = _MockScraper(
        mock_client,
        listings=[{"title": "Job A"}],
    )

    scraper_b = _MockScraper(
        mock_client,
        listings=[{"title": "Job B"}],
    )

    service = ScraperService(mock_client)

    results = service.scrape_many([scraper_a, scraper_b])

    assert len(results) == 2
    assert scraper_a.scrape_calls == 1
    assert scraper_b.scrape_calls == 1


def test_scrape_many_partial_failure() -> None:
    """Verify failed scraper does not stop remaining scrapers."""
    mock_client = MagicMock(spec=HttpClient)

    scraper_a = _MockScraper(
        mock_client,
        listings=[{"title": "Job A"}],
    )

    scraper_fail = _MockScraper(
        mock_client,
        should_fail=True,
    )

    scraper_b = _MockScraper(
        mock_client,
        listings=[{"title": "Job B"}],
    )

    service = ScraperService(mock_client)

    results = service.scrape_many(
        [
            scraper_a,
            scraper_fail,
            scraper_b,
        ]
    )

    assert len(results) == 2
    assert results[0]["title"] == "Job A"
    assert results[1]["title"] == "Job B"


def test_scrape_many_non_scraper_error_propagation() -> None:
    """Verify unexpected exceptions propagate."""
    mock_client = MagicMock(spec=HttpClient)

    scraper_a = _MockScraper(
        mock_client,
        listings=[{"title": "Job A"}],
    )

    scraper_fail = _MockScraper(
        mock_client,
        non_scraper_error=True,
    )

    scraper_b = _MockScraper(
        mock_client,
        listings=[{"title": "Job B"}],
    )

    service = ScraperService(mock_client)

    with pytest.raises(ValueError):
        service.scrape_many(
            [
                scraper_a,
                scraper_fail,
                scraper_b,
            ]
        )


def test_scrape_many_empty() -> None:
    """Verify empty scraper list returns an empty result."""
    mock_client = MagicMock(spec=HttpClient)
    service = ScraperService(mock_client)

    assert service.scrape_many([]) == []
