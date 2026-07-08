"""Pydantic schemas for Internship model serialization."""

from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

__all__ = ["InternshipResponse"]


class InternshipResponse(BaseModel):
    """Pydantic schema representing a serialized internship listing."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 42,
                "company": "Google",
                "title": "Software Engineering Intern",
                "location": "Mountain View, CA",
                "employment_type": "internship",
                "work_mode": "hybrid",
                "url": "https://careers.google.com/jobs/42",
                "posted_date": "2026-07-08",
                "deadline": None,
                "stipend": "$50/hr",
                "skills": "Python, SQL, Algorithms",
                "source": "greenhouse",
                "status": "new",
                "first_seen": "2026-07-08T11:00:00Z",
                "last_seen": "2026-07-08T11:00:00Z",
                "created_at": "2026-07-08T11:00:00Z",
                "updated_at": "2026-07-08T11:00:00Z",
            }
        },
    )

    id: int = Field(description="Unique database identifier for this internship.")
    company: str = Field(description="Name of the company offering the internship.")
    title: str = Field(description="Title of the internship position.")
    location: str | None = Field(
        None,
        description="Geographic location of the internship (e.g. San Francisco, CA).",
    )
    employment_type: str = Field(
        description="Employment type classification (e.g. internship, full-time).",
    )
    work_mode: str = Field(
        description="Work arrangement structure (e.g. remote, hybrid, on-site).",
    )
    url: str = Field(description="Canonical URL for the internship posting.")
    posted_date: date | None = Field(
        None,
        description="Original date when the listing was posted.",
    )
    deadline: date | None = Field(
        None,
        description="Application deadline date, if known.",
    )
    stipend: str | None = Field(
        None,
        description="Stipend or salary details parsed from the listing.",
    )
    skills: str | None = Field(
        None,
        description="Extracted key skills or keywords required for the role.",
    )
    source: str = Field(
        description="Identifies which ATS or website scraper discovered this listing.",
    )
    status: str = Field(
        description="Pipeline processing status (e.g. new, active, archived).",
    )
    first_seen: datetime = Field(
        description="UTC datetime indicating when this listing was first discovered.",
    )
    last_seen: datetime = Field(
        description="UTC datetime indicating when this listing was last seen by the scraper.",
    )
    created_at: datetime = Field(
        description="UTC datetime representing DB record creation.",
    )
    updated_at: datetime = Field(
        description="UTC datetime representing DB record last modification.",
    )
