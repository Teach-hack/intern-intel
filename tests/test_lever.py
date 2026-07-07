"""Unit tests for the LeverScraper."""

from __future__ import annotations

import json
from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.exceptions import (
    ScraperBlockedError,
    ScraperParsingError,
)
from app.core.http_client import HttpClient
from app.scrapers.lever import LeverScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = LeverScraper(mock_http, site_slug="google")
    assert scraper.site_slug == "google"
    assert scraper.company_name == "google"
    assert scraper.get_source_name() == "lever"
    assert scraper._source_url == "https://api.lever.co/v0/postings/google?mode=json"

    # Check explicit company_name
    scraper_explicit = LeverScraper(
        mock_http, site_slug="google", company_name="Google LLC"
    )
    assert scraper_explicit.company_name == "Google LLC"


def test_parse_listings_success() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test")

    payload = [
        {"id": "1", "text": "Job 1", "hostedUrl": "https://example.com/1"},
        {"id": "2", "text": "Job 2", "hostedUrl": "https://example.com/2"},
    ]

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["id"] == "1"
    assert results[1]["text"] == "Job 2"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-list root
    with pytest.raises(
        ScraperParsingError, match="Lever API response root must be a JSON array"
    ):
        scraper.parse_listings("{}")


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard remote internship with workplaceType remote
        (
            {
                "text": "Software Engineering Intern",
                "hostedUrl": "https://jobs.lever.co/test/1",
                "workplaceType": "remote",
                "categories": {"location": "San Francisco, CA"},
                "createdAt": 1783382400000,
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://jobs.lever.co/test/1",
                "location": "San Francisco, CA",
                "employment_type": "internship",
                "work_mode": "remote",
                "source": "lever",
                "status": "new",
                "posted_date": date(2026, 7, 7),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # On-site full-time job with workplaceType on-site
        (
            {
                "text": "Senior Backend Developer (Full-Time)",
                "hostedUrl": "https://jobs.lever.co/test/2",
                "workplaceType": "on-site",
                "categories": {"location": "New York, NY", "commitment": "Full-time"},
            },
            {
                "company": "Test Company",
                "title": "Senior Backend Developer (Full-Time)",
                "url": "https://jobs.lever.co/test/2",
                "location": "New York, NY",
                "employment_type": "full-time",
                "work_mode": "on-site",
                "source": "lever",
                "status": "new",
                "posted_date": None,
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Hybrid contract job inferred from keywords
        (
            {
                "text": "Contract Frontend Engineer (Hybrid)",
                "hostedUrl": "https://jobs.lever.co/test/3",
                "categories": {"location": "Austin, TX"},
            },
            {
                "company": "Test Company",
                "title": "Contract Frontend Engineer (Hybrid)",
                "url": "https://jobs.lever.co/test/3",
                "location": "Austin, TX",
                "employment_type": "contract",
                "work_mode": "hybrid",
                "source": "lever",
                "status": "new",
                "posted_date": None,
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Part-time unknown work mode with date from updatedAt ISO string
        (
            {
                "text": "QA Assistant (Part Time)",
                "hostedUrl": "https://jobs.lever.co/test/4",
                "updatedAt": "2026-07-07T10:00:00Z",
            },
            {
                "company": "Test Company",
                "title": "QA Assistant (Part Time)",
                "url": "https://jobs.lever.co/test/4",
                "location": None,
                "employment_type": "part-time",
                "work_mode": "unknown",
                "source": "lever",
                "status": "new",
                "posted_date": date(2026, 7, 7),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Numeric seconds timestamp instead of milliseconds
        (
            {
                "text": "Data Scientist Intern",
                "hostedUrl": "https://jobs.lever.co/test/5",
                "createdAt": 1783382400.0,
            },
            {
                "company": "Test Company",
                "title": "Data Scientist Intern",
                "url": "https://jobs.lever.co/test/5",
                "location": None,
                "employment_type": "internship",
                "work_mode": "unknown",
                "source": "lever",
                "status": "new",
                "posted_date": date(2026, 7, 7),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Numeric string timestamp in milliseconds
        (
            {
                "text": "Data Analyst Intern",
                "hostedUrl": "https://jobs.lever.co/test/6",
                "createdAt": "1783382400000",
            },
            {
                "company": "Test Company",
                "title": "Data Analyst Intern",
                "url": "https://jobs.lever.co/test/6",
                "location": None,
                "employment_type": "internship",
                "work_mode": "unknown",
                "source": "lever",
                "status": "new",
                "posted_date": date(2026, 7, 7),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
    ],
)
def test_normalize_success(raw_job: dict[str, Any], expected: dict[str, Any]) -> None:
    """Verify that normalize correctly parses details, location, and metadata."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test", company_name="Test Company")

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError for malformed listings."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test")

    # Not a dict
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]

    # Missing text/title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'text'"):
        scraper.normalize({"hostedUrl": "https://example.com/job"})

    # Empty text/title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'text'"):
        scraper.normalize({"text": "  ", "hostedUrl": "https://example.com/job"})

    # Missing URL
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'hostedUrl'"):
        scraper.normalize({"text": "Engineer"})

    # Empty URL
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'hostedUrl'"):
        scraper.normalize({"text": "Engineer", "hostedUrl": "  "})


def test_normalize_date_parsing_warning() -> None:
    """Verify that date parsing handles malformed date strings gracefully by logging a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test", company_name="Test Company")

    raw_job = {
        "text": "Engineer",
        "hostedUrl": "https://example.com/job",
        "updatedAt": "not-a-date",
    }

    with patch("app.scrapers.lever.logger") as mock_logger:
        normalized = scraper.normalize(raw_job)

        # Verify it still returns a normalized dictionary but with posted_date=None
        assert normalized["posted_date"] is None
        mock_logger.warning.assert_called_once()
        assert "Failed to parse date string" in mock_logger.warning.call_args[0][0]


def test_normalize_numeric_date_parsing_warning() -> None:
    """Verify that numeric date parsing handles overflows or errors gracefully."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test", company_name="Test Company")

    # Extreme value to trigger overflow or ValueError
    raw_job = {
        "text": "Engineer",
        "hostedUrl": "https://example.com/job",
        "createdAt": 999999999999999,
    }

    with patch("app.scrapers.lever.logger") as mock_logger:
        normalized = scraper.normalize(raw_job)

        assert normalized["posted_date"] is None
        mock_logger.warning.assert_called_once()
        assert "Failed to parse timestamp" in mock_logger.warning.call_args[0][0]


def test_scrape_flow_integration() -> None:
    """Verify that scrape successfully fetches, parses, normalizes, and validates job listings."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = [
        {
            "text": "Software Intern",
            "hostedUrl": "https://jobs.lever.co/test/jobs/1",
            "categories": {"location": "Remote"},
        },
        {
            "text": "SWE Intern",
            "hostedUrl": "https://jobs.lever.co/test/jobs/2",
            "categories": {"location": "London"},
        },
    ]
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = LeverScraper(mock_http, site_slug="test", company_name="Test Company")
    results = scraper.scrape()

    assert len(results) == 2
    assert results[0]["title"] == "Software Intern"
    assert results[0]["work_mode"] == "remote"
    assert results[0]["company"] == "Test Company"
    assert results[1]["title"] == "SWE Intern"
    assert results[1]["work_mode"] == "unknown"


def test_scrape_empty_jobs() -> None:
    """Verify that scrape handles an empty jobs list successfully."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = json.dumps([])
    mock_http.get.return_value = mock_response

    scraper = LeverScraper(mock_http, site_slug="test")
    results = scraper.scrape()
    assert results == []


def test_scrape_invalid_json() -> None:
    """Verify that scrape handles invalid JSON by raising ScraperParsingError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "{invalid json"
    mock_http.get.return_value = mock_response

    scraper = LeverScraper(mock_http, site_slug="test")
    with pytest.raises(ScraperParsingError):
        scraper.scrape()


def test_scrape_partial_failure() -> None:
    """Verify that a single malformed job does not cause the entire scrape to fail."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = [
        {
            "text": "Valid Intern",
            "hostedUrl": "https://jobs.lever.co/test/jobs/1",
        },
        {
            # Missing title (invalid)
            "hostedUrl": "https://jobs.lever.co/test/jobs/2",
        },
        {
            "text": "Another Valid",
            "hostedUrl": "https://jobs.lever.co/test/jobs/3",
        },
    ]
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = LeverScraper(mock_http, site_slug="test")
    results = scraper.scrape()
    assert len(results) == 2
    assert results[0]["title"] == "Valid Intern"
    assert results[1]["title"] == "Another Valid"


def test_scrape_blocked_403() -> None:
    """Verify that a 403 status code raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_http.get.return_value = mock_response

    scraper = LeverScraper(mock_http, site_slug="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 403"):
        scraper.scrape()


def test_scrape_blocked_429() -> None:
    """Verify that a 429 status code raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = "Too Many Requests"
    mock_http.get.return_value = mock_response

    scraper = LeverScraper(mock_http, site_slug="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 429"):
        scraper.scrape()


def test_normalize_missing_location_and_updated_at() -> None:
    """Verify that normalize handles missing location and updated_at fields gracefully."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test", company_name="Test Company")

    raw_job = {
        "text": "Engineer",
        "hostedUrl": "https://example.com/job",
    }

    normalized = scraper.normalize(raw_job)
    assert normalized["location"] is None
    assert normalized["posted_date"] is None
    assert normalized["title"] == "Engineer"


def test_normalize_date_parsing_z_suffix() -> None:
    """Verify that normalize correctly parses ISO 8601 timestamps ending in 'Z'."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = LeverScraper(mock_http, site_slug="test", company_name="Test Company")

    raw_job = {
        "text": "Engineer",
        "hostedUrl": "https://example.com/job",
        "updatedAt": "2026-07-07T10:00:00Z",
    }

    normalized = scraper.normalize(raw_job)
    assert normalized["posted_date"] == date(2026, 7, 7)
