"""Saved Internship ORM model."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def _utc_now() -> datetime:
    """Return the current timezone-naive UTC timestamp."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SavedJob(Base):
    """Represents an internship listing saved by a user."""

    __tablename__ = "saved_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    internship_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("internships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    user = relationship("User", back_populates="saved_jobs")
    internship = relationship("Internship", back_populates="saved_by")

    __table_args__ = (
        UniqueConstraint("user_id", "internship_id", name="uq_user_internship_saved"),
    )
