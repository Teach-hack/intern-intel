"""Scraper implementation for the Lever ATS job board."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["LeverScraper"]


class LeverScraper(BaseScraper):
    """Scraper for the Lever Applicant Tracking System (ATS) job boards.

    Fetches published job postings from the Lever public postings API
    and normalizes them into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        site_slug: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the Lever scraper.

        Args:
            http_client: Centralized HTTP client instance.
            site_slug: The site slug (slug) for the company on Lever.
            company_name: The display name of the company. If not provided,
                defaults to the site_slug.
        """
        self.site_slug = site_slug
        self.company_name = company_name or site_slug
        source_url = f"https://api.lever.co/v0/postings/{site_slug}?mode=json"
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "lever".
        """
        return "lever"

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw job listings from Lever JSON response content.

        Args:
            content: The raw JSON string from the Lever postings API.

        Returns:
            A list of raw job dictionaries.

        Raises:
            ScraperParsingError: If the JSON is invalid or is not a list.
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ScraperParsingError(f"Invalid JSON content received: {exc}") from exc

        if not isinstance(data, list):
            raise ScraperParsingError("Lever API response root must be a JSON array")

        return data

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a Lever raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the Lever API.

        Returns:
            A dictionary matching the Internship schema.

        Raises:
            ScraperParsingError: If essential fields are missing or invalid in raw.
        """
        if not isinstance(raw, dict):
            raise ScraperParsingError("Raw listing is not a dictionary")

        title = raw.get("text")
        if not isinstance(title, str) or not title.strip():
            raise ScraperParsingError(
                "Missing or invalid 'text' (title) in Lever job listing"
            )
        title = title.strip()

        url = raw.get("hostedUrl")
        if not isinstance(url, str) or not url.strip():
            raise ScraperParsingError(
                "Missing or invalid 'hostedUrl' in Lever job listing"
            )
        url = url.strip()

        location = None
        categories = raw.get("categories")
        if isinstance(categories, dict):
            location_val = categories.get("location")
            if isinstance(location_val, str) and location_val.strip():
                location = location_val.strip()

        location_lower = location.lower() if location else ""
        title_lower = title.lower()

        work_mode = "unknown"
        raw_workplace = raw.get("workplaceType")
        if isinstance(raw_workplace, str) and raw_workplace.strip():
            raw_workplace_clean = raw_workplace.strip().lower()
            if raw_workplace_clean in ("remote", "hybrid"):
                work_mode = raw_workplace_clean
            elif raw_workplace_clean in ("on-site", "onsite"):
                work_mode = "on-site"

        if work_mode == "unknown":
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
        commitment = None
        if isinstance(categories, dict):
            commitment_val = categories.get("commitment")
            if isinstance(commitment_val, str) and commitment_val.strip():
                commitment = commitment_val.strip().lower()

        if commitment:
            if any(term in commitment for term in ("full-time", "full time")):
                employment_type = "full-time"
            elif any(term in commitment for term in ("part-time", "part time")):
                employment_type = "part-time"
            elif "contract" in commitment:
                employment_type = "contract"
            elif any(
                term in commitment for term in ("intern", "internship", "co-op", "coop")
            ):
                employment_type = "internship"

        if employment_type == "internship":
            if any(term in title_lower for term in ("full-time", "full time")):
                employment_type = "full-time"
            elif any(term in title_lower for term in ("part-time", "part time")):
                employment_type = "part-time"
            elif "contract" in title_lower:
                employment_type = "contract"

        posted_date = None
        updated_at = raw.get("updatedAt")
        if updated_at is None:
            updated_at = raw.get("createdAt")
        if isinstance(updated_at, (int, float)):
            try:
                timestamp_sec = updated_at / 1000.0 if updated_at > 1e11 else updated_at
                posted_date = datetime.fromtimestamp(
                    timestamp_sec, tz=timezone.utc
                ).date()
            except (ValueError, OSError, OverflowError) as exc:
                logger.warning(
                    "[{}] Failed to parse timestamp '{}' for job '{}': {}",
                    self.get_source_name(),
                    updated_at,
                    title,
                    exc,
                )
        elif isinstance(updated_at, str) and updated_at.strip():
            try:
                val = updated_at.strip()
                if val.isdigit():
                    numeric_timestamp = float(val)
                    timestamp_sec = (
                        numeric_timestamp / 1000.0
                        if numeric_timestamp > 1e11
                        else numeric_timestamp
                    )
                    posted_date = datetime.fromtimestamp(
                        timestamp_sec,
                        tz=timezone.utc,
                    ).date()
                else:
                    timestamp = val.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(timestamp)
                    posted_date = dt.date()
            except (ValueError, OSError, OverflowError) as exc:
                logger.warning(
                    "[{}] Failed to parse date string '{}' for job '{}': {}",
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
