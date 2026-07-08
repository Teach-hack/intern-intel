"""Scraper implementation for the Ashby ATS job board."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["AshbyScraper"]


class AshbyScraper(BaseScraper):
    """Scraper for the Ashby Applicant Tracking System (ATS) job boards.

    Fetches published job postings from the Ashby API and normalizes them
    into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        company_id: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the Ashby scraper.

        Args:
            http_client: Centralized HTTP client instance.
            company_id: The company identifier (slug) on Ashby.
            company_name: The display name of the company. If not provided,
                defaults to the company_id.
        """
        self.company_id = company_id
        self.company_name = company_name or company_id
        source_url = f"https://api.ashbyhq.com/v1/iframe/{company_id}/jobs"
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "ashby".
        """
        return "ashby"

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw job listings from Ashby JSON response content.

        Args:
            content: The raw JSON string from the Ashby iframe postings API.

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
            raise ScraperParsingError("Ashby API response is not a JSON object")

        jobs = data.get("jobs")
        if jobs is None:
            raise ScraperParsingError("Ashby API response is missing the 'jobs' key")
        if not isinstance(jobs, list):
            raise ScraperParsingError("Ashby API response 'jobs' field is not a list")

        return jobs

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize an Ashby raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the Ashby API.

        Returns:
            A dictionary matching the Internship schema.

        Raises:
            ScraperParsingError: If essential fields are missing or invalid in raw.
        """
        if not isinstance(raw, dict):
            raise ScraperParsingError("Raw listing is not a dictionary")

        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ScraperParsingError("Missing or invalid 'title' in Ashby job listing")
        title = title.strip()

        url = raw.get("jobUrl")
        if not isinstance(url, str) or not url.strip():
            raise ScraperParsingError(
                "Missing or invalid 'jobUrl' in Ashby job listing"
            )
        url = url.strip()

        location = None
        raw_location = raw.get("location")
        if isinstance(raw_location, str) and raw_location.strip():
            location = raw_location.strip()
        elif isinstance(raw_location, dict):
            name_val = raw_location.get("name")
            if isinstance(name_val, str) and name_val.strip():
                location = name_val.strip()

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
        raw_emp = raw.get("employmentType")
        if isinstance(raw_emp, str) and raw_emp.strip():
            raw_emp_clean = raw_emp.strip().lower()
            if any(term in raw_emp_clean for term in ("full-time", "fulltime")):
                employment_type = "full-time"
            elif any(term in raw_emp_clean for term in ("part-time", "parttime")):
                employment_type = "part-time"
            elif "contract" in raw_emp_clean:
                employment_type = "contract"

        # Refine employment type if title has explicit commitment details
        if employment_type == "internship":
            if any(term in title_lower for term in ("full-time", "full time")):
                employment_type = "full-time"
            elif any(term in title_lower for term in ("part-time", "part time")):
                employment_type = "part-time"
            elif "contract" in title_lower:
                employment_type = "contract"

        posted_date = None
        published_at = raw.get("publishedAt")
        if isinstance(published_at, str) and published_at.strip():
            try:
                timestamp = published_at.strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(timestamp)
                posted_date = dt.date()
            except ValueError as exc:
                logger.warning(
                    "[{}] Failed to parse published date '{}' for job '{}': {}",
                    self.get_source_name(),
                    published_at,
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
