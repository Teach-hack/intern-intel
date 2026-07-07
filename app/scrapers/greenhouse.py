"""Scraper implementation for the Greenhouse ATS job board."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["GreenhouseScraper"]


class GreenhouseScraper(BaseScraper):
    """Scraper for the Greenhouse Applicant Tracking System (ATS) job boards.

    Fetches published job postings from the Greenhouse public job board API
    and normalizes them into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        board_token: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the Greenhouse scraper.

        Args:
            http_client: Centralized HTTP client instance.
            board_token: The board token (slug) for the company on Greenhouse.
            company_name: The display name of the company. If not provided,
                defaults to the board_token.
        """
        self.board_token = board_token
        self.company_name = company_name or board_token
        source_url = (
            "https://boards-api.greenhouse.io/v1/boards/"
            f"{board_token}/jobs?content=true&pay_transparency=true"
        )
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "greenhouse".
        """
        return "greenhouse"

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw job listings from Greenhouse JSON response content.

        Args:
            content: The raw JSON string from the Greenhouse job board API.

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
            raise ScraperParsingError("Greenhouse API response is not a JSON object")

        jobs = data.get("jobs")

        if jobs is None:
            raise ScraperParsingError(
                "Greenhouse API response is missing the 'jobs' key"
            )
        if not isinstance(jobs, list):
            raise ScraperParsingError(
                "Greenhouse API response 'jobs' field is not a list"
            )

        return jobs

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a Greenhouse raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the Greenhouse API.

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
                "Missing or invalid 'title' in Greenhouse job listing"
            )
        title = title.strip()

        url = raw.get("absolute_url")
        if not isinstance(url, str) or not url.strip():
            raise ScraperParsingError(
                "Missing or invalid 'absolute_url' in Greenhouse job listing"
            )
        url = url.strip()

        location = None
        raw_location = raw.get("location")
        if isinstance(raw_location, dict):
            location_val = raw_location.get("name")
            if isinstance(location_val, str) and location_val.strip():
                location = location_val.strip()

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

        posted_date = None
        updated_at = raw.get("updated_at")
        if isinstance(updated_at, str) and updated_at.strip():
            try:
                timestamp = updated_at.strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(timestamp)
                posted_date = dt.date()
            except ValueError as exc:
                logger.warning(
                    "[{}] Failed to parse posted date '{}' for job '{}': {}",
                    self.get_source_name(),
                    updated_at,
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
