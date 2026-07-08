"""Unit tests for the SmartRecruitersScraper."""

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
from app.scrapers.smartrecruiters import SmartRecruitersScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = SmartRecruitersScraper(mock_http, company_id="google")
    assert scraper.company_id == "google"
    assert scraper.company_name == "google"
    assert scraper.get_source_name() == "smartrecruiters"
    assert (
        scraper._source_url
        == "https://api.smartrecruiters.com/v1/companies/google/postings"
    )

    # Check explicit company_name
    scraper_explicit = SmartRecruitersScraper(
        mock_http, company_id="google", company_name="Google LLC"
    )
    assert scraper_explicit.company_name == "Google LLC"


def test_parse_listings_success() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SmartRecruitersScraper(mock_http, company_id="test")

    payload = {
        "content": [
            {"name": "Job 1", "id": "1"},
            {"name": "Job 2", "id": "2"},
        ]
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["name"] == "Job 1"
    assert results[1]["id"] == "2"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SmartRecruitersScraper(mock_http, company_id="test")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-dict root
    with pytest.raises(
        ScraperParsingError, match="SmartRecruiters API response is not a JSON object"
    ):
        scraper.parse_listings("[]")

    # Missing content key
    with pytest.raises(
        ScraperParsingError,
        match="SmartRecruiters API response is missing the 'content' key",
    ):
        scraper.parse_listings("{}")

    # Non-list content field
    with pytest.raises(
        ScraperParsingError,
        match="SmartRecruiters API response 'content' field is not a list",
    ):
        scraper.parse_listings('{"content": {}}')


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard remote internship with workplaceType remote
        (
            {
                "name": "Software Engineering Intern",
                "id": "1",
                "location": {
                    "city": "Berlin",
                    "region": "Berlin",
                    "country": "Germany",
                },
                "typeOfEmployment": {"id": "permanent"},
                "releasedDate": "2026-07-07T00:00:00.000Z",
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://jobs.smartrecruiters.com/test/1",
                "location": "Berlin, Berlin, Germany",
                "employment_type": "full-time",
                "work_mode": "unknown",
                "source": "smartrecruiters",
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
                "name": "Data Science Intern (Remote)",
                "id": "2",
                "location": {
                    "city": "San Francisco",
                    "country": "United States",
                },
                "typeOfEmployment": {"id": "temporary"},
                "releasedDate": "2026-07-08T09:00:00+00:00",
            },
            {
                "company": "Test Company",
                "title": "Data Science Intern (Remote)",
                "url": "https://jobs.smartrecruiters.com/test/2",
                "location": "San Francisco, United States",
                "employment_type": "part-time",
                "work_mode": "remote",
                "source": "smartrecruiters",
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
                "name": "Contract Software Engineer (Hybrid)",
                "id": "3",
                "location": {"city": "New York"},
                "typeOfEmployment": {"id": "contract"},
                "releasedDate": "2026-07-08",
            },
            {
                "company": "Test Company",
                "title": "Contract Software Engineer (Hybrid)",
                "url": "https://jobs.smartrecruiters.com/test/3",
                "location": "New York",
                "employment_type": "contract",
                "work_mode": "hybrid",
                "source": "smartrecruiters",
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
    scraper = SmartRecruitersScraper(
        mock_http, company_id="test", company_name="Test Company"
    )

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError on invalid payloads."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SmartRecruitersScraper(mock_http, company_id="test")

    # Non-dict raw job
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore[arg-type]

    # Missing name (title)
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'name'"):
        scraper.normalize({"id": "1"})

    # Missing id
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'id'"):
        scraper.normalize({"name": "Job"})


def test_normalize_unrecognized_date_logs_warning() -> None:
    """Verify that unrecognized date formats result in posted_date=None and log a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SmartRecruitersScraper(mock_http, company_id="test")

    raw_job = {
        "name": "Job",
        "id": "1",
        "releasedDate": "Invalid date string",
    }

    with patch("app.scrapers.smartrecruiters.logger") as mock_logger:
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

    scraper = SmartRecruitersScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 403"):
        scraper.scrape()


def test_scrape_blocked_429() -> None:
    """Verify that a 429 response raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = "Blocked"
    mock_http.get.return_value = mock_response

    scraper = SmartRecruitersScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 429"):
        scraper.scrape()


def test_scrape_success_e2e() -> None:
    """Verify that the full scrape() lifecycle successfully parses, normalizes, and filters."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = {
        "content": [
            {
                "name": "Software Engineer Intern",
                "id": "1",
                "location": {"city": "Remote"},
                "releasedDate": "2026-07-08",
            },
            {
                "name": "Invalid Job due to missing id",
            },
            {
                "name": "Intern",
                "id": "2",
                "releasedDate": "2026-07-08T09:00:00Z",
            },
        ]
    }
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = SmartRecruitersScraper(
        mock_http, company_id="test", company_name="SRCorp"
    )
    results = scraper.scrape()

    assert len(results) == 2
    assert results[0]["title"] == "Software Engineer Intern"
    assert results[0]["url"] == "https://jobs.smartrecruiters.com/test/1"
    assert results[1]["title"] == "Intern"
    assert results[1]["url"] == "https://jobs.smartrecruiters.com/test/2"
