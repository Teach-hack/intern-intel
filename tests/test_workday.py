"""Unit tests for the WorkdayScraper."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.exceptions import (
    ScraperBlockedError,
    ScraperParsingError,
)
from app.core.http_client import HttpClient
from app.scrapers.workday import WorkdayScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = WorkdayScraper(mock_http, tenant="google", parent_site_id="external")
    assert scraper.tenant == "google"
    assert scraper.parent_site_id == "external"
    assert scraper.company_name == "google"
    assert scraper.get_source_name() == "workday"
    assert (
        scraper._source_url
        == "https://google.myworkdayjobs.com/wday/cxs/google/external/jobs"
    )

    # Check explicit company_name
    scraper_explicit = WorkdayScraper(
        mock_http, tenant="google", parent_site_id="external", company_name="Google LLC"
    )
    assert scraper_explicit.company_name == "Google LLC"


def test_parse_listings_success() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = WorkdayScraper(mock_http, tenant="test", parent_site_id="site")

    payload = {
        "jobPostings": [
            {"title": "Job 1", "externalPath": "/job/1"},
            {"title": "Job 2", "externalPath": "/job/2"},
        ]
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["title"] == "Job 1"
    assert results[1]["externalPath"] == "/job/2"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = WorkdayScraper(mock_http, tenant="test", parent_site_id="site")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-dict root
    with pytest.raises(
        ScraperParsingError, match="Workday API response is not a JSON object"
    ):
        scraper.parse_listings("[]")

    # Missing jobPostings key
    with pytest.raises(
        ScraperParsingError,
        match="Workday API response is missing the 'jobPostings' key",
    ):
        scraper.parse_listings("{}")

    # Non-list jobPostings field
    with pytest.raises(
        ScraperParsingError,
        match="Workday API response 'jobPostings' field is not a list",
    ):
        scraper.parse_listings('{"jobPostings": {}}')


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard remote internship
        (
            {
                "title": "Software Engineering Intern",
                "externalPath": "/job/test/1",
                "locationsText": "Remote, US",
                "postedOn": "2026-07-07",
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://test.myworkdayjobs.com/job/test/1",
                "location": "Remote, US",
                "employment_type": "internship",
                "work_mode": "remote",
                "source": "workday",
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
                "title": "Full-Time Staff Engineer (On-Site)",
                "externalPath": "https://example.com/job/2",
                "locationsText": "London, UK",
                "postedOn": "Posted Today",
            },
            {
                "company": "Test Company",
                "title": "Full-Time Staff Engineer (On-Site)",
                "url": "https://example.com/job/2",
                "location": "London, UK",
                "employment_type": "full-time",
                "work_mode": "on-site",
                "source": "workday",
                "status": "new",
                "posted_date": date.today(),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Relative date yesterday
        (
            {
                "title": "Part-Time Contract Intern",
                "externalPath": "/job/3",
                "locationsText": "Office / Hybrid",
                "postedOn": "Posted Yesterday",
            },
            {
                "company": "Test Company",
                "title": "Part-Time Contract Intern",
                "url": "https://test.myworkdayjobs.com/job/3",
                "location": "Office / Hybrid",
                "employment_type": "part-time",
                "work_mode": "hybrid",
                "source": "workday",
                "status": "new",
                "posted_date": date.today() - timedelta(days=1),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Relative date days ago
        (
            {
                "title": "Contractor",
                "externalPath": "/job/4",
                "locationsText": "New York",
                "postedOn": "Posted 5 Days Ago",
            },
            {
                "company": "Test Company",
                "title": "Contractor",
                "url": "https://test.myworkdayjobs.com/job/4",
                "location": "New York",
                "employment_type": "contract",
                "work_mode": "unknown",
                "source": "workday",
                "status": "new",
                "posted_date": date.today() - timedelta(days=5),
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
    scraper = WorkdayScraper(
        mock_http, tenant="test", parent_site_id="site", company_name="Test Company"
    )

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError on invalid payloads."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = WorkdayScraper(mock_http, tenant="test", parent_site_id="site")

    # Non-dict raw job
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore[arg-type]

    # Missing title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'title'"):
        scraper.normalize({"externalPath": "/job/1"})

    # Missing externalPath
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'externalPath'"):
        scraper.normalize({"title": "Job"})


def test_normalize_unrecognized_date_logs_warning() -> None:
    """Verify that unrecognized date formats result in posted_date=None and log a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = WorkdayScraper(mock_http, tenant="test", parent_site_id="site")

    raw_job = {
        "title": "Job",
        "externalPath": "/job/1",
        "postedOn": "Unrecognized date format",
    }

    with patch("app.scrapers.workday.logger") as mock_logger:
        normalized = scraper.normalize(raw_job)

    assert normalized["posted_date"] is None
    mock_logger.warning.assert_called_once()


def test_fetch_page_post_block_403() -> None:
    """Verify that a 403 response in fetch_page raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_http.post.return_value = mock_response

    scraper = WorkdayScraper(mock_http, tenant="test", parent_site_id="site")
    assert scraper._source_url is not None

    with pytest.raises(
        ScraperBlockedError, match="Access blocked with status code 403"
    ):
        scraper.fetch_page(scraper._source_url)


def test_fetch_page_post_block_429() -> None:
    """Verify that a 429 response in fetch_page raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_http.post.return_value = mock_response

    scraper = WorkdayScraper(mock_http, tenant="test", parent_site_id="site")
    assert scraper._source_url is not None

    with pytest.raises(
        ScraperBlockedError, match="Access blocked with status code 429"
    ):
        scraper.fetch_page(scraper._source_url)


def test_scrape_success_e2e() -> None:
    """Verify that the full scrape() lifecycle successfully parses, normalizes, and filters."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = {
        "jobPostings": [
            {
                "title": "Software Engineer Intern",
                "externalPath": "/job/1",
                "locationsText": "Remote",
                "postedOn": "2026-07-08",
            },
            {
                "title": "Invalid Job due to missing path",
            },
            {
                "title": "Intern",
                "externalPath": "/job/2",
                "locationsText": "",
                "postedOn": "Posted Today",
            },
        ]
    }
    mock_response.text = json.dumps(payload)
    mock_http.post.return_value = mock_response

    scraper = WorkdayScraper(
        mock_http, tenant="test", parent_site_id="site", company_name="Google"
    )
    results = scraper.scrape()

    assert len(results) == 2
    assert results[0]["title"] == "Software Engineer Intern"
    assert results[0]["url"] == "https://test.myworkdayjobs.com/job/1"
    assert results[1]["title"] == "Intern"
    assert results[1]["url"] == "https://test.myworkdayjobs.com/job/2"
