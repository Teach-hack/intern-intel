"""Scraper implementation for the iCIMS ATS job board."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["IcimsScraper"]


class IcimsScraper(BaseScraper):
    """Scraper for the iCIMS Applicant Tracking System (ATS) job boards.

    Fetches published job postings from the iCIMS REST API search endpoint
    and normalizes them into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        company_id: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the iCIMS scraper.

        Args:
            http_client: Centralized HTTP client instance.
            company_id: The company identifier (slug) on iCIMS.
            company_name: The display name of the company. If not provided,
                defaults to the company_id.
        """
        self.company_id = company_id
        self.company_name = company_name or company_id
        source_url = f"https://api.icims.com/v1/companies/{company_id}/jobs"
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "icims".
        """
        return "icims"

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw job listings from iCIMS JSON response content.

        Args:
            content: The raw JSON string from the iCIMS postings API.

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
            raise ScraperParsingError("iCIMS API response is not a JSON object")

        jobs = data.get("searchResults")
        if jobs is None:
            raise ScraperParsingError(
                "iCIMS API response is missing the 'searchResults' key"
            )
        if not isinstance(jobs, list):
            raise ScraperParsingError(
                "iCIMS API response 'searchResults' field is not a list"
            )

        return jobs

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize an iCIMS raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the iCIMS API.

        Returns:
            A dictionary matching the Internship schema.

        Raises:
            ScraperParsingError: If essential fields are missing or invalid in raw.
        """
        if not isinstance(raw, dict):
            raise ScraperParsingError("Raw listing is not a dictionary")

        title = raw.get("jobTitle")
        if not isinstance(title, str) or not title.strip():
            raise ScraperParsingError(
                "Missing or invalid 'jobTitle' in iCIMS job listing"
            )
        title = title.strip()

        url = raw.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ScraperParsingError("Missing or invalid 'url' in iCIMS job listing")
        url = url.strip()

        location = None
        job_location = raw.get("jobLocation")
        if isinstance(job_location, str) and job_location.strip():
            location = job_location.strip()
        elif isinstance(job_location, dict):
            # Location is sometimes structured, e.g. {"name": "Seattle, WA"} or {"city": "...", "state": "..."}
            name_val = job_location.get("name")
            if isinstance(name_val, str) and name_val.strip():
                location = name_val.strip()
            else:
                parts = []
                for field in ("city", "state", "country"):
                    val = job_location.get(field)
                    if isinstance(val, str) and val.strip():
                        parts.append(val.strip())
                if parts:
                    location = ", ".join(parts)

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
        posted_date_val = raw.get("postedDate")
        if isinstance(posted_date_val, str) and posted_date_val.strip():
            try:
                timestamp = posted_date_val.strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(timestamp)
                posted_date = dt.date()
            except ValueError as exc:
                logger.warning(
                    "[{}] Failed to parse posted date '{}' for job '{}': {}",
                    self.get_source_name(),
                    posted_date_val,
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
