"""Unit tests for the AshbyScraper."""

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
from app.scrapers.ashby import AshbyScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = AshbyScraper(mock_http, company_id="google")
    assert scraper.company_id == "google"
    assert scraper.company_name == "google"
    assert scraper.get_source_name() == "ashby"
    assert scraper._source_url == "https://api.ashbyhq.com/v1/iframe/google/jobs"

    # Check explicit company_name
    scraper_explicit = AshbyScraper(
        mock_http, company_id="google", company_name="Google LLC"
    )
    assert scraper_explicit.company_name == "Google LLC"


def test_parse_listings_success() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = AshbyScraper(mock_http, company_id="test")

    payload = {
        "jobs": [
            {"title": "Job 1", "jobUrl": "https://example.com/1"},
            {"title": "Job 2", "jobUrl": "https://example.com/2"},
        ]
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["title"] == "Job 1"
    assert results[1]["jobUrl"] == "https://example.com/2"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = AshbyScraper(mock_http, company_id="test")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-dict root
    with pytest.raises(
        ScraperParsingError, match="Ashby API response is not a JSON object"
    ):
        scraper.parse_listings("[]")

    # Missing jobs key
    with pytest.raises(
        ScraperParsingError, match="Ashby API response is missing the 'jobs' key"
    ):
        scraper.parse_listings("{}")

    # Non-list jobs field
    with pytest.raises(
        ScraperParsingError, match="Ashby API response 'jobs' field is not a list"
    ):
        scraper.parse_listings('{"jobs": {}}')


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard remote internship with workplaceType remote
        (
            {
                "title": "Software Engineering Intern",
                "jobUrl": "https://jobs.ashbyhq.com/test/1",
                "location": "San Francisco, CA",
                "employmentType": "Full-Time",
                "publishedAt": "2026-07-07T00:00:00.000Z",
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://jobs.ashbyhq.com/test/1",
                "location": "San Francisco, CA",
                "employment_type": "full-time",
                "work_mode": "unknown",
                "source": "ashby",
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
                "title": "Data Science Intern (Remote)",
                "jobUrl": "https://jobs.ashbyhq.com/test/2",
                "location": {"name": "Remote, USA"},
                "employmentType": "Part-Time",
                "publishedAt": "2026-07-08T09:00:00+00:00",
            },
            {
                "company": "Test Company",
                "title": "Data Science Intern (Remote)",
                "url": "https://jobs.ashbyhq.com/test/2",
                "location": "Remote, USA",
                "employment_type": "part-time",
                "work_mode": "remote",
                "source": "ashby",
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
                "title": "Contract Software Engineer (Hybrid)",
                "jobUrl": "https://jobs.ashbyhq.com/test/3",
                "location": "New York, NY",
                "employmentType": "Contract",
                "publishedAt": "2026-07-08",
            },
            {
                "company": "Test Company",
                "title": "Contract Software Engineer (Hybrid)",
                "url": "https://jobs.ashbyhq.com/test/3",
                "location": "New York, NY",
                "employment_type": "contract",
                "work_mode": "hybrid",
                "source": "ashby",
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
    scraper = AshbyScraper(mock_http, company_id="test", company_name="Test Company")

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError on invalid payloads."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = AshbyScraper(mock_http, company_id="test")

    # Non-dict raw job
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore[arg-type]

    # Missing title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'title'"):
        scraper.normalize({"jobUrl": "https://example.com/1"})

    # Missing jobUrl
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'jobUrl'"):
        scraper.normalize({"title": "Job"})


def test_normalize_unrecognized_date_logs_warning() -> None:
    """Verify that unrecognized date formats result in posted_date=None and log a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = AshbyScraper(mock_http, company_id="test")

    raw_job = {
        "title": "Job",
        "jobUrl": "https://example.com/1",
        "publishedAt": "Invalid date string",
    }

    with patch("app.scrapers.ashby.logger") as mock_logger:
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

    scraper = AshbyScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 403"):
        scraper.scrape()


def test_scrape_blocked_429() -> None:
    """Verify that a 429 response raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = "Blocked"
    mock_http.get.return_value = mock_response

    scraper = AshbyScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 429"):
        scraper.scrape()


def test_scrape_success_e2e() -> None:
    """Verify that the full scrape() lifecycle successfully parses, normalizes, and filters."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = {
        "jobs": [
            {
                "title": "Software Engineer Intern",
                "jobUrl": "https://jobs.ashbyhq.com/1",
                "location": "Remote",
                "publishedAt": "2026-07-08",
            },
            {
                "title": "Invalid Job due to missing jobUrl",
            },
            {
                "title": "Intern",
                "jobUrl": "https://jobs.ashbyhq.com/2",
                "publishedAt": "2026-07-08T09:00:00Z",
            },
        ]
    }
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = AshbyScraper(mock_http, company_id="test", company_name="AshbyCorp")
    results = scraper.scrape()

    assert len(results) == 2
    assert results[0]["title"] == "Software Engineer Intern"
    assert results[0]["url"] == "https://jobs.ashbyhq.com/1"
    assert results[1]["title"] == "Intern"
    assert results[1]["url"] == "https://jobs.ashbyhq.com/2"
