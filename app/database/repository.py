"""Repository for managing Internship ORM model operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select

from app.models.internship import Internship

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

__all__ = ["InternshipRepository"]


class InternshipRepository:
    """Repository for performing CRUD operations on Internship entities.

    This repository is responsible only for database operations.
    Transaction management (commit/rollback) must be handled by the caller.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Active SQLAlchemy database session.
        """
        self._session = session

    def add(self, job: Internship) -> Internship:
        """Add a single internship.

        Args:
            job: Internship instance to persist.

        Returns:
            The persisted Internship instance.
        """
        self._session.add(job)
        self._session.flush()
        return job

    def add_many(self, jobs: list[Internship]) -> list[Internship]:
        """Add multiple internship listings.

        Args:
            jobs: Internship instances to persist.

        Returns:
            The persisted Internship instances.
        """
        if not jobs:
            return []

        self._session.add_all(jobs)
        self._session.flush()
        return jobs

    def get(self, id: int) -> Internship | None:
        """Retrieve an internship by ID."""
        return self._session.get(Internship, id)

    def get_by_url(self, url: str) -> Internship | None:
        """Retrieve an internship by its URL.

        Args:
            url: Canonical internship URL.

        Returns:
            Matching Internship if found, otherwise None.
        """
        stmt = select(Internship).where(Internship.url == url).limit(1)

        return self._session.scalar(stmt)

    def get_by_company_and_title(
        self,
        company: str,
        title: str,
    ) -> Internship | None:
        """Retrieve an internship by company and title.

        Args:
            company: Company name.
            title: Internship title.

        Returns:
            Matching Internship if found, otherwise None.
        """
        stmt = (
            select(Internship)
            .where(
                Internship.company == company,
                Internship.title == title,
            )
            .limit(1)
        )

        return self._session.scalar(stmt)

    def get_all(self) -> list[Internship]:
        """Retrieve all internships.

        Returns:
            List of Internship objects.
        """
        stmt = select(Internship).order_by(Internship.id)

        return list(self._session.scalars(stmt).all())

    def delete(self, job: Internship) -> None:
        """Delete an internship.

        Args:
            job: Internship instance to remove.
        """
        self._session.delete(job)
        self._session.flush()

    def delete_all(self) -> int:
        """Delete all internship listings.

        Returns:
            Number of deleted rows.
        """
        stmt = delete(Internship)

        result = self._session.execute(stmt)
        self._session.flush()

        deleted = result.rowcount  # type: ignore[attr-defined]

        if deleted is None:
            return 0

        return int(deleted)

    def count(self) -> int:
        """Return total internship count.

        Returns:
            Number of internship records.
        """
        stmt = select(func.count(Internship.id))

        total = self._session.scalar(stmt)

        return int(total or 0)

    def exists(self, url: str) -> bool:
        """Check whether an internship exists.

        Args:
            url: Canonical internship URL.

        Returns:
            True if a matching internship exists, otherwise False.
        """
        stmt = select(Internship.id).where(Internship.url == url).limit(1)

        return self._session.scalar(stmt) is not None
