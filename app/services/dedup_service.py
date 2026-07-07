"""Service for deduplicating job listings."""

from __future__ import annotations

from typing import Any

__all__ = ["DedupService"]


class DedupService:
    """Service to deduplicate job listings.

    Deduplication rules:

    1. Exact URL match (when URL is available).
    2. Company + title match (case-insensitive).

    The first occurrence is preserved.
    Invalid or malformed records are ignored.
    """

    def deduplicate(
        self,
        jobs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Deduplicate job listings.

        Args:
            jobs: List of normalized job dictionaries.

        Returns:
            A new list containing only unique job listings.
        """
        seen_urls: set[str] = set()
        seen_company_titles: set[tuple[str, str]] = set()

        deduplicated: list[dict[str, Any]] = []

        for job in jobs:
            if not isinstance(job, dict):
                continue

            company = job.get("company")
            title = job.get("title")
            url = job.get("url")

            if (
                not isinstance(company, str)
                or not isinstance(title, str)
                or not isinstance(url, str)
            ):
                continue

            company_clean = company.strip()
            title_clean = title.strip()
            url_clean = url.strip()

            if not company_clean or not title_clean or not url_clean:
                continue

            company_title_key = (
                company_clean.lower(),
                title_clean.lower(),
            )

            if url_clean in seen_urls:
                continue

            if company_title_key in seen_company_titles:
                continue

            seen_urls.add(url_clean)
            seen_company_titles.add(company_title_key)
            deduplicated.append(job.copy())

        return deduplicated
