"""Unit tests for the BaseScraper abstraction."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.base_scraper import BaseScraper
from app.core.exceptions import (
    HttpTimeoutError,
    ScraperBlockedError,
    ScraperError,
    ScraperParsingError,
)
from app.core.http_client import HttpClient

# ---------------------------------------------------------------------------
# Concrete Test subclass of BaseScraper
# ---------------------------------------------------------------------------


class _ConcreteTestScraper(BaseScraper):
    """A concrete implementation of BaseScraper for testing purposes."""

    def __init__(
        self,
        http_client: HttpClient,
        source_url: str | None = None,
        raw_listings: list[dict[str, Any]] | None = None,
        raise_parse_error: bool = False,
        raise_normalize_error_for_keys: list[str] | None = None,
    ) -> None:
        super().__init__(http_client, source_url)
        self.raw_listings = raw_listings if raw_listings is not None else []
        self.raise_parse_error = raise_parse_error
        self.raise_normalize_error_for_keys = raise_normalize_error_for_keys or []
        self.close_called_count = 0

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        if self.raise_parse_error:
            raise ScraperParsingError("Parsing failed due to bad structure")
        return self.raw_listings

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        key = raw.get("id", "")
        if key in self.raise_normalize_error_for_keys:
            raise ScraperParsingError(f"Normalize error for item {key}")
        # Default normalization maps raw directly or applies a simple map
        return {
            "company": raw.get("company", "Test Company"),
            "title": raw.get("title", "Test Title"),
            "url": raw.get("url", "https://example.com/job"),
            "employment_type": raw.get("employment_type", "internship"),
            "work_mode": raw.get("work_mode", "remote"),
            "source": self.get_source_name(),
            "status": "new",
        }

    def get_source_name(self) -> str:
        return "test_source"

    def close(self) -> None:
        super().close()
        self.close_called_count += 1


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


def test_successful_scrape() -> None:
    """Verify that a successful scrape execution follows the correct lifecycle."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "raw page content"
    mock_http.get.return_value = mock_response

    raw_listings = [
        {
            "id": "1",
            "company": "Google",
            "title": "SWE Intern",
            "url": "https://careers.google.com/1",
        },
        {
            "id": "2",
            "company": "Microsoft",
            "title": "PM Intern",
            "url": "https://careers.microsoft.com/2",
        },
    ]

    scraper = _ConcreteTestScraper(http_client=mock_http, raw_listings=raw_listings)
    results = scraper.scrape("https://example.com/jobs")

    assert len(results) == 2
    assert results[0]["company"] == "Google"
    assert results[0]["title"] == "SWE Intern"
    assert results[1]["company"] == "Microsoft"
    assert results[1]["title"] == "PM Intern"

    mock_http.get.assert_called_once_with("https://example.com/jobs")


def test_empty_results() -> None:
    """Verify scrape returns an empty list when parse_listings yields no items."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "empty page"
    mock_http.get.return_value = mock_response

    scraper = _ConcreteTestScraper(http_client=mock_http, raw_listings=[])
    results = scraper.scrape("https://example.com/jobs")

    assert results == []


def test_validation_rejects_missing_required_fields() -> None:
    """Verify that validate() filters out listings that are missing required fields."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "page content"
    mock_http.get.return_value = mock_response

    # Item 1 lacks 'company', Item 2 lacks 'title', Item 3 is valid
    raw_listings = [
        {
            "id": "1",
            "company": "",
            "title": "SWE Intern",
            "url": "https://careers.google.com/1",
        },
        {
            "id": "2",
            "company": "Google",
            "title": "   ",
            "url": "https://careers.google.com/2",
        },
        {
            "id": "3",
            "company": "Google",
            "title": "SWE Intern",
            "url": "https://careers.google.com/3",
        },
    ]

    scraper = _ConcreteTestScraper(http_client=mock_http, raw_listings=raw_listings)
    results = scraper.scrape("https://example.com/jobs")

    assert len(results) == 1
    assert results[0]["url"] == "https://careers.google.com/3"


def test_validation_rejects_non_string() -> None:
    """Verify validate() rejects listings where required fields are not strings."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = _ConcreteTestScraper(http_client=mock_http)

    invalid_listing = {
        "company": "Google",
        "title": 12345,  # Invalid: not a string
        "url": "https://careers.google.com/job",
        "employment_type": "internship",
        "work_mode": "remote",
        "source": "test_source",
        "status": "new",
    }
    assert scraper.validate(invalid_listing) is False


def test_validate_returns_true_for_valid_listing() -> None:
    """Verify validate() returns True for a listing conforming to the required schema."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = _ConcreteTestScraper(http_client=mock_http)

    valid_listing = {
        "company": "Google",
        "title": "SWE Intern",
        "url": "https://careers.google.com/job",
        "employment_type": "internship",
        "work_mode": "remote",
        "source": "test_source",
        "status": "new",
    }
    assert scraper.validate(valid_listing) is True


def test_validation_warning_logging() -> None:
    """Verify that validate() outputs warnings when encountering validation errors."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = _ConcreteTestScraper(http_client=mock_http)

    invalid_listing = {
        "company": "Google",
        "title": "",  # Empty
        "url": "https://careers.google.com/job",
        "employment_type": "internship",
        "work_mode": "remote",
        "source": "test_source",
        "status": "new",
    }

    with patch("app.core.base_scraper.logger") as mock_logger:
        res = scraper.validate(invalid_listing)
        assert res is False
        mock_logger.warning.assert_called_once()
        args = mock_logger.warning.call_args[0]
        # Verify the template string contains formatting placeholders
        assert "Validation failed: required field '{}' is empty" in args[0]
        # Verify format args
        assert args[1] == "test_source"
        assert args[2] == "title"
        # Verify the empty title is logged, not the entire dict
        assert args[3] == ""
        # Verify the url is logged
        assert args[4] == "https://careers.google.com/job"


def test_partial_failure_normalize() -> None:
    """Verify that normalize failure on one item logs and continues with others."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "page content"
    mock_http.get.return_value = mock_response

    # Item 2 will raise a ScraperParsingError in normalize()
    raw_listings = [
        {
            "id": "1",
            "company": "Google",
            "title": "SWE Intern",
            "url": "https://careers.google.com/1",
        },
        {
            "id": "2",
            "company": "Microsoft",
            "title": "PM Intern",
            "url": "https://careers.microsoft.com/2",
        },
        {
            "id": "3",
            "company": "Apple",
            "title": "QA Intern",
            "url": "https://careers.apple.com/3",
        },
    ]

    scraper = _ConcreteTestScraper(
        http_client=mock_http,
        raw_listings=raw_listings,
        raise_normalize_error_for_keys=["2"],
    )
    results = scraper.scrape("https://example.com/jobs")

    assert len(results) == 2
    assert results[0]["company"] == "Google"
    assert results[1]["company"] == "Apple"


def test_unexpected_error_in_normalize_continues() -> None:
    """Verify unexpected non-scraper exceptions in normalize are handled gracefully."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "page content"
    mock_http.get.return_value = mock_response

    raw_listings = [{"id": "1"}]

    scraper = _ConcreteTestScraper(http_client=mock_http, raw_listings=raw_listings)
    # Patch normalize to raise a raw ValueError
    with patch.object(scraper, "normalize", side_effect=ValueError("Unexpected")):
        results = scraper.scrape("https://example.com")
        assert results == []


def test_parse_failure_propagates() -> None:
    """Verify that a parsing exception propagates to the caller as ScraperParsingError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "page content"
    mock_http.get.return_value = mock_response

    scraper = _ConcreteTestScraper(http_client=mock_http, raise_parse_error=True)

    with pytest.raises(
        ScraperParsingError, match="Parsing failed due to bad structure"
    ):
        scraper.scrape("https://example.com/jobs")


def test_fetch_page_blocked_403() -> None:
    """Verify fetch_page raises ScraperBlockedError when target returns 403."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_http.get.return_value = mock_response

    scraper = _ConcreteTestScraper(http_client=mock_http)

    with pytest.raises(
        ScraperBlockedError, match="Access blocked with status code 403"
    ):
        scraper.scrape("https://example.com/blocked")


def test_fetch_page_blocked_429() -> None:
    """Verify fetch_page raises ScraperBlockedError when target returns 429."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = "Too Many Requests"
    mock_http.get.return_value = mock_response

    scraper = _ConcreteTestScraper(http_client=mock_http)

    with pytest.raises(
        ScraperBlockedError, match="Access blocked with status code 429"
    ):
        scraper.scrape("https://example.com/rate-limited")


def test_http_client_exceptions_propagate() -> None:
    """Verify that HTTP transport errors propagate directly to the caller without wrapping."""
    mock_http = MagicMock(spec=HttpClient)
    mock_http.get.side_effect = HttpTimeoutError("GET https://example.com timed out")

    scraper = _ConcreteTestScraper(http_client=mock_http)

    # Let HttpClient exceptions propagate directly
    with pytest.raises(HttpTimeoutError, match="GET https://example.com timed out"):
        scraper.scrape("https://example.com")


def test_default_url_fallback() -> None:
    """Verify scraper uses fallback source_url if scrape() is called without URL."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "default url content"
    mock_http.get.return_value = mock_response

    scraper = _ConcreteTestScraper(
        http_client=mock_http, source_url="https://example.com/default"
    )
    results = scraper.scrape()

    assert results == []
    mock_http.get.assert_called_once_with("https://example.com/default")


def test_no_url_raises_scraper_error() -> None:
    """Verify ScraperError is raised if no URL is provided anywhere."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = _ConcreteTestScraper(http_client=mock_http, source_url=None)

    with pytest.raises(
        ScraperError, match="No scraping URL provided and no default URL configured"
    ):
        scraper.scrape()


def test_close_and_subclass_resources() -> None:
    """Verify close() lifecycle hook can be called multiple times without raising."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = _ConcreteTestScraper(http_client=mock_http)

    scraper.close()
    scraper.close()

    assert scraper.close_called_count == 2
    # Ensure it doesn't close the shared HttpClient
    mock_http.close.assert_not_called()


def test_dependency_injection_preserves_client() -> None:
    """Verify the scraper retains the exact HttpClient reference injected."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = _ConcreteTestScraper(http_client=mock_http)
    assert scraper._http_client is mock_http


def test_logging_calls_during_scrape() -> None:
    """Verify logging functions are triggered at correct lifecycle steps."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "page content"
    mock_http.get.return_value = mock_response

    raw_listings = [
        {
            "id": "1",
            "company": "Google",
            "title": "SWE",
            "url": "https://careers.google.com/1",
        },
    ]
    scraper = _ConcreteTestScraper(http_client=mock_http, raw_listings=raw_listings)

    with patch("app.core.base_scraper.logger") as mock_logger:
        scraper.scrape("https://example.com")

        # Must log debug for starting workflow and raw listing count
        assert mock_logger.debug.call_count >= 2
        # Must log info for completion statistics
        mock_logger.info.assert_called_once()


def test_lifecycle_order() -> None:
    """Verify that calling scrape() executes steps in sequence (fetch -> parse -> normalize -> validate)."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "raw page text"
    mock_http.get.return_value = mock_response

    raw_listings = [{"id": "1", "company": "G", "title": "T", "url": "https://url"}]

    call_sequence: list[str] = []

    class _TrackedScraper(BaseScraper):
        """Minimal scraper used to verify lifecycle ordering."""

        def parse_listings(self, content: str) -> list[dict[str, Any]]:
            call_sequence.append("parse")
            return raw_listings

        def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
            call_sequence.append("normalize")
            return {
                "company": "Google",
                "title": "SWE",
                "url": "https://example.com/job",
                "employment_type": "internship",
                "work_mode": "remote",
                "source": "test_source",
                "status": "new",
            }

        def get_source_name(self) -> str:
            return "test_source"

    scraper = _TrackedScraper(http_client=mock_http)

    def mock_fetch_page(url: str) -> str:
        call_sequence.append("fetch")
        return "raw"

    def mock_validate(listing: dict[str, Any]) -> bool:
        call_sequence.append("validate")
        return True

    with patch.object(
        scraper,
        "fetch_page",
        side_effect=mock_fetch_page,
    ) as mock_fetch:
        with patch.object(
            scraper,
            "validate",
            side_effect=mock_validate,
        ) as mock_validate_patch:
            scraper.scrape("https://example.com")

            assert call_sequence == ["fetch", "parse", "normalize", "validate"]
            mock_fetch.assert_called_once()
            mock_validate_patch.assert_called_once()
