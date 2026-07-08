"""Scraper implementation for the SAP SuccessFactors ATS job board."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core.base_scraper import BaseScraper
from app.core.exceptions import ScraperParsingError
from app.core.http_client import HttpClient
from app.core.logger import logger

__all__ = ["SuccessFactorsScraper"]


class SuccessFactorsScraper(BaseScraper):
    """Scraper for the SAP SuccessFactors Applicant Tracking System (ATS).

    Fetches published job postings from the SuccessFactors JSON REST/OData API
    and normalizes them into the canonical Internship schema.
    """

    def __init__(
        self,
        http_client: HttpClient,
        company_id: str,
        company_name: str | None = None,
    ) -> None:
        """Initialize the SuccessFactors scraper.

        Args:
            http_client: Centralized HTTP client instance.
            company_id: The company identifier (tenant) on SuccessFactors.
            company_name: The display name of the company. If not provided,
                defaults to the company_id.
        """
        self.company_id = company_id
        self.company_name = company_name or company_id
        source_url = f"https://api.successfactors.eu/odata/v2/JobRequisition?company={company_id}"
        super().__init__(http_client, source_url=source_url)

    def get_source_name(self) -> str:
        """Return the stable lowercase source identifier for this scraper.

        Returns:
            A stable string identifying this scraper, which is "successfactors".
        """
        return "successfactors"

    def parse_listings(self, content: str) -> list[dict[str, Any]]:
        """Parse raw job listings from SuccessFactors JSON response content.

        Supports both standard JSON lists and OData wrapped lists.

        Args:
            content: The raw JSON string from the SuccessFactors API.

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
                "SuccessFactors API response is not a JSON object"
            )

        # Support OData v2 wrapping {"d": {"results": [...]}}
        d_val = data.get("d")
        if isinstance(d_val, dict):
            results = d_val.get("results")
            if isinstance(results, list):
                return results

        # Support standard list wrapping {"jobs": [...] }
        jobs = data.get("jobs")
        if isinstance(jobs, list):
            return jobs

        raise ScraperParsingError(
            "SuccessFactors API response must contain a list under 'd.results' or 'jobs'"
        )

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a SuccessFactors raw job listing into the canonical schema.

        Args:
            raw: A single raw job listing from the SuccessFactors API.

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
                "Missing or invalid 'title' in SuccessFactors job listing"
            )
        title = title.strip()

        job_id = raw.get("jobId")
        if not job_id:
            raise ScraperParsingError(
                "Missing or invalid 'jobId' in SuccessFactors job listing"
            )
        job_id_str = str(job_id).strip()

        # Resolve URL: prefer jobUrl or construct one
        url = raw.get("jobUrl")
        if not isinstance(url, str) or not url.strip():
            url = (
                f"https://career.successfactors.eu/career?company={self.company_id}"
                f"&career_ns=job_listing&career_job_req_id={job_id_str}"
            )
        else:
            url = url.strip()

        location = None
        raw_location = raw.get("location") or raw.get("jobLocation")
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
        if any(term in title_lower for term in ("full-time", "full time")):
            employment_type = "full-time"
        elif any(term in title_lower for term in ("part-time", "part time")):
            employment_type = "part-time"
        elif "contract" in title_lower:
            employment_type = "contract"

        posted_date = None
        posting_date = raw.get("postingDate")
        if isinstance(posting_date, str) and posting_date.strip():
            try:
                # OData dates are sometimes formatted like "/Date(1625788800000)/"
                val = posting_date.strip()
                if "/Date(" in val:
                    start_idx = val.find("(") + 1
                    end_idx = val.find(")")
                    epoch_ms = int(val[start_idx:end_idx].split("+")[0].split("-")[0])
                    posted_date = datetime.fromtimestamp(epoch_ms / 1000.0).date()
                else:
                    timestamp = val.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(timestamp)
                    posted_date = dt.date()
            except Exception as exc:
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
