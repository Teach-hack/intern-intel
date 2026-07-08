"""Unit tests for the IcimsScraper."""

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
from app.scrapers.icims import IcimsScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = IcimsScraper(mock_http, company_id="google")
    assert scraper.company_id == "google"
    assert scraper.company_name == "google"
    assert scraper.get_source_name() == "icims"
    assert scraper._source_url == "https://api.icims.com/v1/companies/google/jobs"

    # Check explicit company_name
    scraper_explicit = IcimsScraper(
        mock_http, company_id="google", company_name="Google LLC"
    )
    assert scraper_explicit.company_name == "Google LLC"


def test_parse_listings_success() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = IcimsScraper(mock_http, company_id="test")

    payload = {
        "searchResults": [
            {"jobTitle": "Job 1", "url": "https://example.com/1"},
            {"jobTitle": "Job 2", "url": "https://example.com/2"},
        ]
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["jobTitle"] == "Job 1"
    assert results[1]["url"] == "https://example.com/2"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = IcimsScraper(mock_http, company_id="test")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-dict root
    with pytest.raises(
        ScraperParsingError, match="iCIMS API response is not a JSON object"
    ):
        scraper.parse_listings("[]")

    # Missing searchResults key
    with pytest.raises(
        ScraperParsingError,
        match="iCIMS API response is missing the 'searchResults' key",
    ):
        scraper.parse_listings("{}")

    # Non-list searchResults field
    with pytest.raises(
        ScraperParsingError,
        match="iCIMS API response 'searchResults' field is not a list",
    ):
        scraper.parse_listings('{"searchResults": {}}')


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard remote internship with workplaceType remote
        (
            {
                "jobTitle": "Software Engineering Intern",
                "url": "https://jobs.icims.com/test/1",
                "jobLocation": {
                    "city": "Dallas",
                    "state": "TX",
                    "country": "US",
                },
                "employmentType": "Full-Time",
                "postedDate": "2026-07-07T00:00:00.000Z",
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://jobs.icims.com/test/1",
                "location": "Dallas, TX, US",
                "employment_type": "full-time",
                "work_mode": "unknown",
                "source": "icims",
                "status": "new",
                "posted_date": date(2026, 7, 7),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Remote Part-Time Internship
        (
            {
                "jobTitle": "Data Science Intern (Remote)",
                "url": "https://jobs.icims.com/test/2",
                "jobLocation": "Remote, US",
                "employmentType": "Part-Time",
                "postedDate": "2026-07-08T09:00:00+00:00",
            },
            {
                "company": "Test Company",
                "title": "Data Science Intern (Remote)",
                "url": "https://jobs.icims.com/test/2",
                "location": "Remote, US",
                "employment_type": "part-time",
                "work_mode": "remote",
                "source": "icims",
                "status": "new",
                "posted_date": date(2026, 7, 8),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Hybrid contract
        (
            {
                "jobTitle": "Contract Software Engineer (Hybrid)",
                "url": "https://jobs.icims.com/test/3",
                "jobLocation": {"name": "Seattle"},
                "employmentType": "Contract",
                "postedDate": "2026-07-08",
            },
            {
                "company": "Test Company",
                "title": "Contract Software Engineer (Hybrid)",
                "url": "https://jobs.icims.com/test/3",
                "location": "Seattle",
                "employment_type": "contract",
                "work_mode": "hybrid",
                "source": "icims",
                "status": "new",
                "posted_date": date(2026, 7, 8),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
    ],
)
def test_normalize_success(raw_job: dict[str, Any], expected: dict[str, Any]) -> None:
    """Verify that normalize correctly structures raw data into standard schema."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = IcimsScraper(mock_http, company_id="test", company_name="Test Company")

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError on invalid payloads."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = IcimsScraper(mock_http, company_id="test")

    # Non-dict raw job
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore[arg-type]

    # Missing jobTitle
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'jobTitle'"):
        scraper.normalize({"url": "https://example.com/1"})

    # Missing url
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'url'"):
        scraper.normalize({"jobTitle": "Job"})


def test_normalize_unrecognized_date_logs_warning() -> None:
    """Verify that unrecognized date formats result in posted_date=None and log a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = IcimsScraper(mock_http, company_id="test")

    raw_job = {
        "jobTitle": "Job",
        "url": "https://example.com/1",
        "postedDate": "Invalid date string",
    }

    with patch("app.scrapers.icims.logger") as mock_logger:
        normalized = scraper.normalize(raw_job)

    assert normalized["posted_date"] is None
    mock_logger.warning.assert_called_once()


def test_scrape_blocked_403() -> None:
    """Verify that a 403 response raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_response.text = "Blocked"
    mock_http.get.return_value = mock_response

    scraper = IcimsScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 403"):
        scraper.scrape()


def test_scrape_blocked_429() -> None:
    """Verify that a 429 response raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = "Blocked"
    mock_http.get.return_value = mock_response

    scraper = IcimsScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 429"):
        scraper.scrape()


def test_scrape_success_e2e() -> None:
    """Verify that the full scrape() lifecycle successfully parses, normalizes, and filters."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = {
        "searchResults": [
            {
                "jobTitle": "Software Engineer Intern",
                "url": "https://jobs.icims.com/1",
                "jobLocation": "Remote",
                "postedDate": "2026-07-08",
            },
            {
                "jobTitle": "Invalid Job due to missing url",
            },
            {
                "jobTitle": "Intern",
                "url": "https://jobs.icims.com/2",
                "postedDate": "2026-07-08T09:00:00Z",
            },
        ]
    }
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = IcimsScraper(mock_http, company_id="test", company_name="iCIMSCorp")
    results = scraper.scrape()

    assert len(results) == 2
    assert results[0]["title"] == "Software Engineer Intern"
    assert results[0]["url"] == "https://jobs.icims.com/1"
    assert results[1]["title"] == "Intern"
    assert results[1]["url"] == "https://jobs.icims.com/2"
