"""Scraper implementation for the SmartRecruiters ATS job board."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["SmartRecruitersScraper"]


class SmartRecruitersScraper(BaseScraper):
    """Scraper for the SmartRecruiters Applicant Tracking System (ATS) job boards.

    Fetches published job postings from the SmartRecruiters public API
    and normalizes them into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        company_id: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the SmartRecruiters scraper.

        Args:
            http_client: Centralized HTTP client instance.
            company_id: The company identifier (slug) on SmartRecruiters.
            company_name: The display name of the company. If not provided,
                defaults to the company_id.
        """
        self.company_id = company_id
        self.company_name = company_name or company_id
        source_url = (
            f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings"
        )
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "smartrecruiters".
        """
        return "smartrecruiters"

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw job listings from SmartRecruiters JSON response content.

        Args:
            content: The raw JSON string from the SmartRecruiters postings API.

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
            raise ScraperParsingError(
                "SmartRecruiters API response is not a JSON object"
            )

        jobs = data.get("content")
        if jobs is None:
            raise ScraperParsingError(
                "SmartRecruiters API response is missing the 'content' key"
            )
        if not isinstance(jobs, list):
            raise ScraperParsingError(
                "SmartRecruiters API response 'content' field is not a list"
            )

        return jobs

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a SmartRecruiters raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the SmartRecruiters API.

        Returns:
            A dictionary matching the Internship schema.

        Raises:
            ScraperParsingError: If essential fields are missing or invalid in raw.
        """
        if not isinstance(raw, dict):
            raise ScraperParsingError("Raw listing is not a dictionary")

        title = raw.get("name")
        if not isinstance(title, str) or not title.strip():
            raise ScraperParsingError(
                "Missing or invalid 'name' (title) in SmartRecruiters job listing"
            )
        title = title.strip()

        job_id = raw.get("id")
        if not isinstance(job_id, str) or not job_id.strip():
            raise ScraperParsingError(
                "Missing or invalid 'id' in SmartRecruiters job listing"
            )
        job_id = job_id.strip()
        url = f"https://jobs.smartrecruiters.com/{self.company_id}/{job_id}"

        location = None
        raw_location = raw.get("location")
        if isinstance(raw_location, dict):
            parts: list[str] = []
            for field in ("city", "region", "country"):
                val = raw_location.get(field)
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
        raw_emp = raw.get("typeOfEmployment")
        if isinstance(raw_emp, dict):
            emp_id = raw_emp.get("id")
            if isinstance(emp_id, str) and emp_id.strip():
                emp_id_clean = emp_id.strip().lower()
                if any(term in emp_id_clean for term in ("full-time", "permanent")):
                    employment_type = "full-time"
                elif any(term in emp_id_clean for term in ("part-time", "temporary")):
                    employment_type = "part-time"
                elif "contract" in emp_id_clean:
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
        released_date = raw.get("releasedDate")
        if isinstance(released_date, str) and released_date.strip():
            try:
                timestamp = released_date.strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(timestamp)
                posted_date = dt.date()
            except ValueError as exc:
                logger.warning(
                    "[{}] Failed to parse released date '{}' for job '{}': {}",
                    self.get_source_name(),
                    released_date,
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
