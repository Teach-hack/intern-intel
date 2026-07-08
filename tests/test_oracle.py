"""Unit tests for the OracleScraper."""

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
from app.scrapers.oracle import OracleScraper


def test_initialization() -> None:
    """Verify that initialization sets properties correctly."""
    mock_http = MagicMock(spec=HttpClient)

    # Check default company_name
    scraper = OracleScraper(mock_http, company_id="google")
    assert scraper.company_id == "google"
    assert scraper.company_name == "google"
    assert scraper.get_source_name() == "oracle"
    assert (
        scraper._source_url
        == "https://google.fa.ocs.oraclecloud.com/hcmRestApi/resources/portal/jobs"
    )

    # Check explicit company_name
    scraper_explicit = OracleScraper(
        mock_http, company_id="google", company_name="Google LLC"
    )
    assert scraper_explicit.company_name == "Google LLC"


def test_parse_listings_success() -> None:
    """Verify that parse_listings correctly extracts job dicts from valid JSON."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = OracleScraper(mock_http, company_id="test")

    payload = {
        "items": [
            {"Title": "Job 1", "Id": "1", "RequisitionNumber": "REQ1"},
            {"Title": "Job 2", "Id": "2", "RequisitionNumber": "REQ2"},
        ]
    }

    content = json.dumps(payload)
    results = scraper.parse_listings(content)
    assert len(results) == 2
    assert results[0]["Title"] == "Job 1"
    assert results[1]["RequisitionNumber"] == "REQ2"


def test_parse_listings_failures() -> None:
    """Verify that parse_listings raises ScraperParsingError on malformed JSON or structure."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = OracleScraper(mock_http, company_id="test")

    # Invalid JSON
    with pytest.raises(ScraperParsingError, match="Invalid JSON content received"):
        scraper.parse_listings("{invalid json")

    # Non-dict root
    with pytest.raises(
        ScraperParsingError, match="Oracle API response is not a JSON object"
    ):
        scraper.parse_listings("[]")

    # Missing items key
    with pytest.raises(
        ScraperParsingError, match="Oracle API response is missing the 'items' key"
    ):
        scraper.parse_listings("{}")

    # Non-list items field
    with pytest.raises(
        ScraperParsingError, match="Oracle API response 'items' field is not a list"
    ):
        scraper.parse_listings('{"items": {}}')


@pytest.mark.parametrize(
    ("raw_job", "expected"),
    [
        # Standard remote internship with workplaceType remote
        (
            {
                "Title": "Software Engineering Intern",
                "Id": "1",
                "RequisitionNumber": "REQ1",
                "PrimaryLocation": "Chicago, IL",
                "PostingDate": "2026-07-07T00:00:00.000Z",
            },
            {
                "company": "Test Company",
                "title": "Software Engineering Intern",
                "url": "https://test.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/REQ1",
                "location": "Chicago, IL",
                "employment_type": "internship",
                "work_mode": "unknown",
                "source": "oracle",
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
                "Title": "Data Science Intern (Remote)",
                "Id": "2",
                "PrimaryLocation": "Remote, USA",
                "PostingDate": "2026-07-08T09:00:00+00:00",
            },
            {
                "company": "Test Company",
                "title": "Data Science Intern (Remote)",
                "url": "https://test.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/2",
                "location": "Remote, USA",
                "employment_type": "internship",
                "work_mode": "remote",
                "source": "oracle",
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
                "Title": "Contract Software Engineer (Hybrid)",
                "RequisitionNumber": "REQ3",
                "PrimaryLocation": "New York",
                "PostingDate": "2026-07-08",
            },
            {
                "company": "Test Company",
                "title": "Contract Software Engineer (Hybrid)",
                "url": "https://test.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/REQ3",
                "location": "New York",
                "employment_type": "contract",
                "work_mode": "hybrid",
                "source": "oracle",
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
    scraper = OracleScraper(mock_http, company_id="test", company_name="Test Company")

    normalized = scraper.normalize(raw_job)
    assert normalized == expected


def test_normalize_failures() -> None:
    """Verify that normalize raises ScraperParsingError on invalid payloads."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = OracleScraper(mock_http, company_id="test")

    # Non-dict raw job
    with pytest.raises(ScraperParsingError, match="Raw listing is not a dictionary"):
        scraper.normalize([])  # type: ignore[arg-type]

    # Missing Title
    with pytest.raises(ScraperParsingError, match="Missing or invalid 'Title'"):
        scraper.normalize({"Id": "1"})

    # Missing both RequisitionNumber and Id
    with pytest.raises(
        ScraperParsingError,
        match="Missing both 'RequisitionNumber' and 'Id'",
    ):
        scraper.normalize({"Title": "Job"})


def test_normalize_unrecognized_date_logs_warning() -> None:
    """Verify that unrecognized date formats result in posted_date=None and log a warning."""
    mock_http = MagicMock(spec=HttpClient)
    scraper = OracleScraper(mock_http, company_id="test")

    raw_job = {
        "Title": "Job",
        "Id": "1",
        "PostingDate": "Invalid date string",
    }

    with patch("app.scrapers.oracle.logger") as mock_logger:
        normalized = scraper.normalize(raw_job)

    assert normalized["posted_date"] is None
    mock_logger.warning.assert_called_once()


def test_fetch_page_post_block_403() -> None:
    """Verify that a 403 response in fetch_page raises ScraperBlockedError."""
    mock_http = MagicMock(spec=HttpClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_http.post.return_value = mock_response

    scraper = OracleScraper(mock_http, company_id="test")
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

    scraper = OracleScraper(mock_http, company_id="test")
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
        "items": [
            {
                "Title": "Software Engineer Intern",
                "Id": "1",
                "PrimaryLocation": "Remote",
                "PostingDate": "2026-07-08",
            },
            {
                "Title": "Invalid Job due to missing id",
            },
            {
                "Title": "Intern",
                "Id": "2",
                "PrimaryLocation": "",
                "PostingDate": "2026-07-08T09:00:00Z",
            },
        ]
    }
    mock_response.text = json.dumps(payload)
    mock_http.post.return_value = mock_response

    scraper = OracleScraper(mock_http, company_id="test", company_name="OracleCorp")
    results = scraper.scrape()

    assert len(results) == 2
    assert results[0]["title"] == "Software Engineer Intern"
    assert (
        results[0]["url"]
        == "https://test.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/1"
    )
    assert results[1]["title"] == "Intern"
    assert (
        results[1]["url"]
        == "https://test.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/2"
    )
