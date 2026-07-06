"""Internship ORM model."""

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Internship(Base):
    """Represents a scraped internship listing stored for tracking and deduplication."""

    __tablename__ = "internships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="Company name as scraped from the source",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        index=True,
        comment="Job or internship title",
    )
    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        comment="Geographic location or region, if available",
    )
    employment_type: Mapped[str] = mapped_column(
        String(50),
        comment="Employment classification, e.g. internship or full-time",
    )
    work_mode: Mapped[str] = mapped_column(
        String(50),
        comment="Work arrangement, e.g. remote, hybrid, or on-site",
    )
    url: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        comment="Canonical URL used for deduplication",
    )
    posted_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date the listing was originally posted, if known",
    )
    deadline: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Application deadline, if published",
    )
    stipend: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Stipend or compensation text as shown on the source",
    )
    skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Skills or requirements extracted from the listing",
    )
    source: Mapped[str] = mapped_column(
        String(100),
        comment="Scraper or platform identifier that found this listing",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        comment="Pipeline status, e.g. new, active, or archived",
    )
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        comment="UTC timestamp when this listing was first discovered",
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        comment="UTC timestamp when this listing was last observed in a scrape",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        comment="UTC timestamp when this row was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        comment="UTC timestamp when this row was last modified",
    )
