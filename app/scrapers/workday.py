"""Scraper implementation for the Workday ATS job board."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperBlockedError, ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["WorkdayScraper"]


class WorkdayScraper(BaseScraper):
    """Scraper for the Workday Applicant Tracking System (ATS) job boards.

    Fetches published job postings from the Workday JSON REST API via POST
    requests and normalizes them into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        tenant: str,
        parent_site_id: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the Workday scraper.

        Args:
            http_client: Centralized HTTP client instance.
            tenant: The Workday tenant identifier.
            parent_site_id: The Workday parent site identifier (e.g. "external").
            company_name: The display name of the company. If not provided,
                defaults to the tenant name.
        """
        self.tenant = tenant
        self.parent_site_id = parent_site_id
        self.company_name = company_name or tenant
        source_url = (
            f"https://{tenant}.myworkdayjobs.com/wday/cxs/"
            f"{tenant}/{parent_site_id}/jobs"
        )
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "workday".
        """
        return "workday"

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
        """Parse raw job listings from Workday JSON response content.

        Args:
            content: The raw JSON string from the Workday postings API.

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
            raise ScraperParsingError("Workday API response is not a JSON object")

        jobs = data.get("jobPostings")
        if jobs is None:
            raise ScraperParsingError(
                "Workday API response is missing the 'jobPostings' key"
            )
        if not isinstance(jobs, list):
            raise ScraperParsingError(
                "Workday API response 'jobPostings' field is not a list"
            )

        return jobs

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a Workday raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the Workday API.

        Returns:
            A dictionary matching the Internship schema.

        Raises:
            ScraperParsingError: If essential fields are missing or invalid in raw.
        """
        if not isinstance(raw, dict):
            raise ScraperParsingError("Raw listing is not a dictionary")

        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ScraperParsingError(
                "Missing or invalid 'title' in Workday job listing"
            )
        title = title.strip()

        external_path = raw.get("externalPath")
        if not isinstance(external_path, str) or not external_path.strip():
            raise ScraperParsingError(
                "Missing or invalid 'externalPath' in Workday job listing"
            )
        external_path = external_path.strip()
        url = (
            external_path
            if external_path.startswith("http")
            else f"https://{self.tenant}.myworkdayjobs.com{external_path}"
        )

        location = None
        locations_text = raw.get("locationsText")
        if isinstance(locations_text, str) and locations_text.strip():
            location = locations_text.strip()

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
        if any(term in title_lower for term in ("full-time", "full time")):
            employment_type = "full-time"
        elif any(term in title_lower for term in ("part-time", "part time")):
            employment_type = "part-time"
        elif "contract" in title_lower:
            employment_type = "contract"

        # Try parsing dates (often formatted like "Posted 5 Days Ago" or ISO formats)
        posted_date = None
        posted_on = raw.get("postedOn")
        if isinstance(posted_on, str) and posted_on.strip():
            posted_on_clean = posted_on.strip()
            try:
                posted_date = datetime.fromisoformat(posted_on_clean).date()
            except ValueError:
                # Relative date fallback
                today = date.today()
                if "today" in posted_on_clean.lower():
                    posted_date = today
                elif "yesterday" in posted_on_clean.lower():
                    posted_date = today - timedelta(days=1)
                elif "day" in posted_on_clean.lower():
                    parts = [int(s) for s in posted_on_clean.split() if s.isdigit()]
                    if parts:
                        posted_date = today - timedelta(days=parts[0])
                else:
                    logger.warning(
                        "[{}] Unrecognized postedOn format '{}' for job '{}'",
                        self.get_source_name(),
                        posted_on_clean,
                        title,
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
