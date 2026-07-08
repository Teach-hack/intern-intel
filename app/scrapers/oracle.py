"""Scraper implementation for the Oracle Cloud Careers ATS job board."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperBlockedError, ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["OracleScraper"]


class OracleScraper(BaseScraper):
    """Scraper for the Oracle Cloud Careers Applicant Tracking System (ATS).

    Fetches published job postings from the Oracle Cloud Careers JSON REST API
    via POST requests and normalizes them into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        company_id: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the Oracle scraper.

        Args:
            http_client: Centralized HTTP client instance.
            company_id: The company identifier (tenant/subdomain) on Oracle Cloud.
            company_name: The display name of the company. If not provided,
                defaults to the company_id.
        """
        self.company_id = company_id
        self.company_name = company_name or company_id
        source_url = f"https://{company_id}.fa.ocs.oraclecloud.com/hcmRestApi/resources/portal/jobs"
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "oracle".
        """
        return "oracle"

    def fetch_page(self, url: str) -> str:
        """Fetch the page content for a given URL via a POST request.

        Args:
            url: The target URL to fetch.

        Returns:
            The raw text content of the response.

        Raises:
            ScraperBlockedError: If the remote site returns 403 or 429.
            HttpClientError: Propagated directly from the HTTP Client.
        """
        response = self._http_client.post(
            url,
            json={"limit": 100, "offset": 0, "searchText": ""},
        )
        if response.status_code in (403, 429):
            raise ScraperBlockedError(
                f"Access blocked with status code {response.status_code}"
            )
        return response.text

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw job listings from Oracle JSON response content.

        Args:
            content: The raw JSON string from the Oracle REST API.

        Returns:
            A list of raw job dictionaries.

        Raises:
            ScraperParsingError: If the JSON is invalid or missing required keys.
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ScraperParsingError(f"Invalid JSON content received: {exc}") from exc

        if not isinstance(data, dict):
            raise ScraperParsingError("Oracle API response is not a JSON object")

        jobs = data.get("items")
        if jobs is None:
            raise ScraperParsingError("Oracle API response is missing the 'items' key")
        if not isinstance(jobs, list):
            raise ScraperParsingError("Oracle API response 'items' field is not a list")

        return jobs

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize an Oracle raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the Oracle API.

        Returns:
            A dictionary matching the Internship schema.

        Raises:
            ScraperParsingError: If essential fields are missing or invalid in raw.
        """
        if not isinstance(raw, dict):
            raise ScraperParsingError("Raw listing is not a dictionary")

        title = raw.get("Title")
        if not isinstance(title, str) or not title.strip():
            raise ScraperParsingError(
                "Missing or invalid 'Title' in Oracle job listing"
            )
        title = title.strip()

        # Try to resolve requisition number or job ID
        req_num = raw.get("RequisitionNumber")
        raw_id = raw.get("Id")
        if not req_num and not raw_id:
            raise ScraperParsingError(
                "Missing both 'RequisitionNumber' and 'Id' in Oracle job listing"
            )

        ident = str(req_num or raw_id).strip()
        url = (
            f"https://{self.company_id}.fa.ocs.oraclecloud.com/hcmUI/"
            f"CandidateExperience/en/sites/CX/job/{ident}"
        )

        location = None
        primary_location = raw.get("PrimaryLocation")
        if isinstance(primary_location, str) and primary_location.strip():
            location = primary_location.strip()

        location_lower = location.lower() if location else ""
        title_lower = title.lower()

        work_mode = "unknown"
        if "remote" in location_lower or "remote" in title_lower:
            work_mode = "remote"
        elif "hybrid" in location_lower or "hybrid" in title_lower:
            work_mode = "hybrid"
        elif any(
            keyword in location_lower or keyword in title_lower
            for keyword in ("on-site", "onsite", "office")
        ):
            work_mode = "on-site"

        employment_type = "internship"
        # Extract from title or custom properties
        if any(term in title_lower for term in ("full-time", "full time")):
            employment_type = "full-time"
        elif any(term in title_lower for term in ("part-time", "part time")):
            employment_type = "part-time"
        elif "contract" in title_lower:
            employment_type = "contract"

        posted_date = None
        posting_date = raw.get("PostingDate")
        if isinstance(posting_date, str) and posting_date.strip():
            try:
                timestamp = posting_date.strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(timestamp)
                posted_date = dt.date()
            except ValueError as exc:
                logger.warning(
                    "[{}] Failed to parse posting date '{}' for job '{}': {}",
                    self.get_source_name(),
                    posting_date,
                    title,
                    exc,
                )

        return {
            "company": self.company_name,
            "title": title,
            "url": url,
            "location": location,
            "employment_type": employment_type,
            "work_mode": work_mode,
            "source": self.get_source_name(),
            "status": "new",
            "posted_date": posted_date,
            "deadline": None,
            "stipend": None,
            "skills": None,
        }
