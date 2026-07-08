"""Unit tests for the SuccessFactorsScraper."""

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
from app.scrapers.successfactors import SuccessFactorsScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = SuccessFactorsScraper(mock_http, company_id="sap")
    assert scraper.company_id == "sap"
    assert scraper.company_name == "sap"
    assert scraper.get_source_name() == "successfactors"
    assert (
        scraper._source_url
        == "https://api.successfactors.eu/odata/v2/JobRequisition?company=sap"
    )

    # Check explicit company_name
    scraper_explicit = SuccessFactorsScraper(
        mock_http, company_id="sap", company_name="SAP SE"
    )
    assert scraper_explicit.company_name == "SAP SE"


def test_parse_listings_success_odata() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid OData JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SuccessFactorsScraper(mock_http, company_id="test")

    payload = {
        "d": {
            "results": [
                {"title": "Job 1", "jobId": "1"},
                {"title": "Job 2", "jobId": "2"},
            ]
        }
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["title"] == "Job 1"
    assert results[1]["jobId"] == "2"


def test_parse_listings_success_standard() -> None:
    """Verify that parse_listings correctly extracts job dicts from standard JSON list."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SuccessFactorsScraper(mock_http, company_id="test")

    payload = {
        "jobs": [
            {"title": "Job A", "jobId": "A"},
            {"title": "Job B", "jobId": "B"},
        ]
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["title"] == "Job A"
    assert results[1]["jobId"] == "B"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SuccessFactorsScraper(mock_http, company_id="test")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-dict root
    with pytest.raises(
        ScraperParsingError, match="SuccessFactors API response is not a JSON object"
    ):
        scraper.parse_listings("[]")

    # Missing results and jobs keys
    with pytest.raises(
        ScraperParsingError,
        match="SuccessFactors API response must contain a list under 'd.results' or 'jobs'",
    ):
        scraper.parse_listings("{}")


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard OData response with timestamp date `/Date(1783382400000)/` (2026-07-07)
        (
            {
                "title": "Software Engineering Intern",
                "jobId": "1234",
                "jobUrl": "https://careers.sap.com/job/1234",
                "location": "Walldorf, Germany",
                "postingDate": "/Date(1783382400000)/",
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://careers.sap.com/job/1234",
                "location": "Walldorf, Germany",
                "employment_type": "internship",
                "work_mode": "unknown",
                "source": "successfactors",
                "status": "new",
                "posted_date": date(2026, 7, 7),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Remote Part-Time Internship with ISO date
        (
            {
                "title": "Data Science Intern (Remote)",
                "jobId": "5678",
                "jobLocation": {"name": "Remote, US"},
                "postingDate": "2026-07-08T09:00:00+00:00",
            },
            {
                "company": "Test Company",
                "title": "Data Science Intern (Remote)",
                "url": "https://career.successfactors.eu/career?company=test&career_ns=job_listing&career_job_req_id=5678",
                "location": "Remote, US",
                "employment_type": "internship",
                "work_mode": "remote",
                "source": "successfactors",
                "status": "new",
                "posted_date": date(2026, 7, 8),
                "deadline": None,
                "stipend": None,
                "skills": None,
            },
        ),
        # Hybrid full-time
        (
            {
                "title": "Full-Time Software Engineer (Hybrid)",
                "jobId": "999",
                "jobLocation": "New York",
                "postingDate": "2026-07-08",
            },
            {
                "company": "Test Company",
                "title": "Full-Time Software Engineer (Hybrid)",
                "url": "https://career.successfactors.eu/career?company=test&career_ns=job_listing&career_job_req_id=999",
                "location": "New York",
                "employment_type": "full-time",
                "work_mode": "hybrid",
                "source": "successfactors",
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
    scraper = SuccessFactorsScraper(
        mock_http, company_id="test", company_name="Test Company"
    )

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError on invalid payloads."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SuccessFactorsScraper(mock_http, company_id="test")

    # Non-dict raw job
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore[arg-type]

    # Missing title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'title'"):
        scraper.normalize({"jobId": "1"})

    # Missing jobId
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'jobId'"):
        scraper.normalize({"title": "Job"})


def test_normalize_unrecognized_date_logs_warning() -> None:
    """Verify that unrecognized date formats result in posted_date=None and log a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = SuccessFactorsScraper(mock_http, company_id="test")

    raw_job = {
        "title": "Job",
        "jobId": "1",
        "postingDate": "Invalid date string",
    }

    with patch("app.scrapers.successfactors.logger") as mock_logger:
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

    scraper = SuccessFactorsScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 403"):
        scraper.scrape()


def test_scrape_blocked_429() -> None:
    """Verify that a 429 response raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.text = "Blocked"
    mock_http.get.return_value = mock_response

    scraper = SuccessFactorsScraper(mock_http, company_id="test")

    with pytest.raises(ScraperBlockedError, match="blocked with status code 429"):
        scraper.scrape()


def test_scrape_success_e2e() -> None:
    """Verify that the full scrape() lifecycle successfully parses, normalizes, and filters."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    payload = {
        "d": {
            "results": [
                {
                    "title": "Software Engineer Intern",
                    "jobId": "1",
                    "location": "Remote",
                    "postingDate": "2026-07-08",
                },
                {
                    "title": "Invalid Job due to missing jobId",
                },
                {
                    "title": "Intern",
                    "jobId": "2",
                    "postingDate": "2026-07-08T09:00:00Z",
                },
            ]
        }
    }
    mock_response.text = json.dumps(payload)
    mock_http.get.return_value = mock_response

    scraper = SuccessFactorsScraper(mock_http, company_id="test", company_name="SFC")
    results = scraper.scrape()

    assert len(results) == 2
    assert results[0]["title"] == "Software Engineer Intern"
    assert results[1]["title"] == "Intern"
