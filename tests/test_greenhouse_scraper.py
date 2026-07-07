"""Unit tests for the GreenhouseScraper."""

from __future__ import annotations

import json
from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.exceptions import ScraperParsingError
from app.core.http_client import HttpClient
from app.scrapers.greenhouse import GreenhouseScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = GreenhouseScraper(mock_http, board_token="google")
    assert scraper.board_token == "google"
    assert scraper.company_name == "google"
    assert scraper.get_source_name() == "greenhouse"
    assert (
        scraper._source_url
        == "https://boards-api.greenhouse.io/v1/boards/google/jobs?content=true&pay_transparency=true"
    )

    # Check explicit company_name
    scraper_explicit = GreenhouseScraper(
        mock_http, board_token="google", company_name="Google LLC"
    )
    assert scraper_explicit.company_name == "Google LLC"


def test_parse_listings_success() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = GreenhouseScraper(mock_http, board_token="test")

    payload = {
        "jobs": [
            {"id": 1, "title": "Job 1", "absolute_url": "https://example.com/1"},
            {"id": 2, "title": "Job 2", "absolute_url": "https://example.com/2"},
        ],
        "meta": {"total": 2},
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["id"] == 1
    assert results[1]["title"] == "Job 2"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = GreenhouseScraper(mock_http, board_token="test")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-dictionary root
    with pytest.raises(
        ScraperParsingError, match="Greenhouse API response is not a JSON object"
    ):
        scraper.parse_listings("[]")

    # Missing "jobs" key
    with pytest.raises(
        ScraperParsingError, match="Greenhouse API response is missing the 'jobs' key"
    ):
        scraper.parse_listings(json.dumps({"meta": {"total": 0}}))

    # "jobs" key is not a list
    with pytest.raises(
        ScraperParsingError, match="Greenhouse API response 'jobs' field is not a list"
    ):
        scraper.parse_listings(json.dumps({"jobs": "not a list"}))


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard remote internship
        (
            {
                "title": "Software Engineering Intern",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/1",
                "location": {"name": "Remote, US"},
                "updated_at": "2026-07-07T10:00:00-05:00",
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://boards.greenhouse.io/test/jobs/1",
                "location": "Remote, US",
                "employment_type": "internship",
                "work_mode": "remote",
                "source": "greenhouse",
                "status": "new",
                "posted_date": date(2026, 7, 7),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # On-site full-time job
        (
            {
                "title": "Senior Backend Developer (Full-Time)",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/2",
                "location": {"name": "New York, NY (On-site)"},
            },
            {
                "company": "Test Company",
                "title": "Senior Backend Developer (Full-Time)",
                "url": "https://boards.greenhouse.io/test/jobs/2",
                "location": "New York, NY (On-site)",
                "employment_type": "full-time",
                "work_mode": "on-site",
                "source": "greenhouse",
                "status": "new",
                "posted_date": None,
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Hybrid contract job with missing location name
        (
            {
                "title": "Hybrid Frontend Engineer Contractor",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/3",
                "location": {"name": ""},
            },
            {
                "company": "Test Company",
                "title": "Hybrid Frontend Engineer Contractor",
                "url": "https://boards.greenhouse.io/test/jobs/3",
                "location": None,
                "employment_type": "contract",
                "work_mode": "hybrid",
                "source": "greenhouse",
                "status": "new",
                "posted_date": None,
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Part-time unknown work mode
        (
            {
                "title": "QA Assistant (Part Time)",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/4",
                "location": None,
            },
            {
                "company": "Test Company",
                "title": "QA Assistant (Part Time)",
                "url": "https://boards.greenhouse.io/test/jobs/4",
                "location": None,
                "employment_type": "part-time",
                "work_mode": "unknown",
                "source": "greenhouse",
                "status": "new",
                "posted_date": None,
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
    scraper = GreenhouseScraper(
        mock_http, board_token="test", company_name="Test Company"
    )

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError for malformed listings."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = GreenhouseScraper(mock_http, board_token="test")

    # Not a dict
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore

    # Missing title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'title'"):
        scraper.normalize({"absolute_url": "https://example.com/job"})

    # Empty title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'title'"):
        scraper.normalize({"title": "  ", "absolute_url": "https://example.com/job"})

    # Missing URL
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'absolute_url'"):
        scraper.normalize({"title": "Engineer"})

    # Empty URL
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'absolute_url'"):
        scraper.normalize({"title": "Engineer", "absolute_url": "  "})


def test_normalize_date_parsing_warning() -> None:
    """Verify that date parsing handles malformed date strings gracefully by logging a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = GreenhouseScraper(
        mock_http, board_token="test", company_name="Test Company"
    )

    raw_job = {
        "title": "Engineer",
        "absolute_url": "https://example.com/job",
        "updated_at": "not-a-date",
    }

    with patch("app.scrapers.greenhouse.logger") as mock_logger:
        normalized = scraper.normalize(raw_job)

        # Verify it still returns a normalized dictionary but with posted_date=None
        assert normalized["posted_date"] is None
        mock_logger.warning.assert_called_once()
        assert "Failed to parse posted date" in mock_logger.warning.call_args[0][0]


def test_scrape_flow_integration() -> None:
    """Verify that scrape successfully fetches, parses, normalizes, and validates job listings."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = {
        "jobs": [
            {
                "title": "Software Intern",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/1",
                "location": {"name": "Remote"},
            },
            {
                "title": "SWE Intern",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/2",
                "location": {"name": "London"},
            },
        ]
    }
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = GreenhouseScraper(
        mock_http, board_token="test", company_name="Test Company"
    )
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
    mock_response.text = json.dumps({"jobs": []})
    mock_http.get.return_value = mock_response

    scraper = GreenhouseScraper(mock_http, board_token="test")
    results = scraper.scrape()
    assert results == []


def test_scrape_invalid_json() -> None:
    """Verify that scrape handles invalid JSON by raising ScraperParsingError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "{invalid json"
    mock_http.get.return_value = mock_response

    scraper = GreenhouseScraper(mock_http, board_token="test")
    with pytest.raises(ScraperParsingError):
        scraper.scrape()


def test_scrape_partial_failure() -> None:
    """Verify that a single malformed job does not cause the entire scrape to fail."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = {
        "jobs": [
            {
                "title": "Valid Intern",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/1",
            },
            {
                # Missing title (invalid)
                "absolute_url": "https://boards.greenhouse.io/test/jobs/2",
            },
            {
                "title": "Another Valid",
                "absolute_url": "https://boards.greenhouse.io/test/jobs/3",
            },
        ]
    }
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = GreenhouseScraper(mock_http, board_token="test")
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

    scraper = GreenhouseScraper(mock_http, board_token="test")
    from app.core.exceptions import ScraperBlockedError

    with pytest.raises(ScraperBlockedError, match="blocked with status code 403"):
        scraper.scrape()


def test_scrape_blocked_429() -> None:
    """Verify that a 429 status code raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = "Too Many Requests"
    mock_http.get.return_value = mock_response

    scraper = GreenhouseScraper(mock_http, board_token="test")
    from app.core.exceptions import ScraperBlockedError

    with pytest.raises(ScraperBlockedError, match="blocked with status code 429"):
        scraper.scrape()


def test_normalize_missing_location_and_updated_at() -> None:
    """Verify that normalize handles missing location and updated_at fields gracefully."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = GreenhouseScraper(
        mock_http, board_token="test", company_name="Test Company"
    )

    raw_job = {
        "title": "Engineer",
        "absolute_url": "https://example.com/job",
    }

    normalized = scraper.normalize(raw_job)
    assert normalized["location"] is None
    assert normalized["posted_date"] is None
    assert normalized["title"] == "Engineer"


def test_normalize_date_parsing_z_suffix() -> None:
    """Verify that normalize correctly parses ISO 8601 timestamps ending in 'Z'."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = GreenhouseScraper(
        mock_http, board_token="test", company_name="Test Company"
    )

    raw_job = {
        "title": "Engineer",
        "absolute_url": "https://example.com/job",
        "updated_at": "2026-07-07T10:00:00Z",
    }

    normalized = scraper.normalize(raw_job)
    assert normalized["posted_date"] == date(2026, 7, 7)
