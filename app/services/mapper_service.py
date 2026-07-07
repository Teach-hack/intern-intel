"""Service for mapping normalized job dictionaries to Internship ORM models."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.models.internship import Internship

__all__ = ["MapperService"]


class MapperService:
    """Map normalized job dictionaries into Internship ORM models."""

    DEFAULT_STATUS = "new"

    def map(self, job: dict[str, Any]) -> Internship:
        """Convert a normalized job dictionary into an Internship model.

        Args:
            job: Normalized job dictionary.

        Returns:
            Internship ORM instance.
        """
        return Internship(
            company=str(job["company"]),
            title=str(job["title"]),
            location=self._optional_str(job.get("location")),
            employment_type=str(job["employment_type"]),
            work_mode=str(job["work_mode"]),
            url=str(job["url"]),
            posted_date=self._optional_date(job.get("posted_date")),
            deadline=self._optional_date(job.get("deadline")),
            stipend=self._optional_str(job.get("stipend")),
            skills=self._optional_str(job.get("skills")),
            source=str(job["source"]),
            status=str(job.get("status", self.DEFAULT_STATUS)),
        )

    def map_many(
        self,
        jobs: list[dict[str, Any]],
    ) -> list[Internship]:
        """Convert multiple normalized job dictionaries.

        Args:
            jobs: List of normalized jobs.

        Returns:
            List of Internship ORM models.
        """
        return [self.map(job) for job in jobs]

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        """Normalize optional string values."""
        if value is None:
            return None

        text = str(value).strip()

        return text or None

    @staticmethod
    def _optional_date(value: Any) -> date | None:
        """Normalize optional date values."""
        if value is None:
            return None

        if isinstance(value, date):
            return value

        return None
