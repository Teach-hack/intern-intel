"""Database service layer for coordinating Internship persistence."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import date
from typing import Any, TYPE_CHECKING

from app.core.logger import logger
from app.database.repository import InternshipRepository
from app.database.session import get_session

if TYPE_CHECKING:
    from app.models.internship import Internship

__all__ = ["DatabaseService"]


class DatabaseService:
    """Service responsible for Internship database operations.

    This service manages database sessions and delegates persistence
    operations to InternshipRepository.
    """

    @contextmanager
    def _repository(self) -> Generator[InternshipRepository, None, None]:
        """Provide a repository with a managed database session."""
        with get_session() as session:
            yield InternshipRepository(session)

    def save(self, job: Internship) -> Internship:
        """Persist a single internship.

        Args:
            job: Internship instance to persist.

        Returns:
            The persisted Internship instance.

        Raises:
            ValueError: If the provided job is None.
        """
        if job is None:
            raise ValueError("job must not be None")

        with self._repository() as repo:
            saved = repo.add(job)

        logger.info(
            "Saved internship | company={} | title={} | url={}",
            saved.company,
            saved.title,
            saved.url,
        )

        return saved

    def save_many(
        self,
        jobs: list[Internship],
    ) -> list[Internship]:
        """Persist multiple internships.

        Args:
            jobs: Internship instances to persist.

        Returns:
            Persisted Internship instances.
        """
        if not jobs:
            logger.debug("No internship listings supplied for bulk save.")
            return []

        with self._repository() as repo:
            saved = repo.add_many(jobs)

        logger.info("Saved {} internship listings.", len(saved))

        return saved

    def exists(self, url: str) -> bool:
        """Check whether a listing exists.

        Args:
            url: Canonical internship URL.

        Returns:
            True if the listing exists.

        Raises:
            ValueError: If URL is empty.
        """
        url = url.strip()

        if not url:
            raise ValueError("url must not be empty")

        with self._repository() as repo:
            exists = repo.exists(url)

        logger.debug("Checked existence for '{}': {}", url, exists)

        return exists

    def get_all(self) -> list[Internship]:
        """Retrieve every stored internship.

        Returns:
            All stored Internship objects.
        """
        with self._repository() as repo:
            jobs = repo.get_all()

        logger.info("Retrieved {} internship listings.", len(jobs))

        return jobs

    def count(self) -> int:
        """Return the total number of internships.

        Returns:
            Total Internship count.
        """
        with self._repository() as repo:
            total = repo.count()

        logger.debug("Current internship count: {}", total)

        return total

    def delete(self, job: Internship) -> None:
        """Delete a single internship.

        Args:
            job: Internship instance to delete.

        Raises:
            ValueError: If job is None.
        """
        if job is None:
            raise ValueError("job must not be None")

        with self._repository() as repo:
            repo.delete(job)

        logger.info(
            "Deleted internship | company={} | title={} | url={}",
            job.company,
            job.title,
            job.url,
        )

    def delete_all(self) -> int:
        """Delete every internship from the database.

        Returns:
            Number of deleted records.
        """
        with self._repository() as repo:
            deleted = repo.delete_all()

        logger.info("Deleted {} internship listings.", deleted)

        return deleted

    def query_internships(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        order: str = "asc",
        company: str | None = None,
        location: str | None = None,
        employment_type: str | None = None,
        source: str | None = None,
        search: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Internship]:
        """Query and filter internships using various criteria.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            sort_by: Field name to sort by.
            order: Sort order ("asc" or "desc").
            company: Filter by company name.
            location: Filter by location (case-insensitive substring).
            employment_type: Filter by employment type.
            source: Filter by scraper source.
            search: Search query string to match in title, company, or skills.
            date_from: Only return internships posted on or after this date.
            date_to: Only return internships posted on or before this date.

        Returns:
            List of matching Internship objects.
        """
        from sqlalchemy import and_, func, or_, select

        from app.models.internship import Internship

        with self._repository() as repo:
            session = repo._session
            stmt = select(Internship)
            conditions = []

            if company:
                conditions.append(
                    func.lower(Internship.company) == company.lower().strip()
                )
            if location:
                conditions.append(
                    func.lower(Internship.location).like(
                        f"%{location.lower().strip()}%"
                    )
                )
            if employment_type:
                conditions.append(
                    func.lower(Internship.employment_type)
                    == employment_type.lower().strip()
                )
            if source:
                conditions.append(
                    func.lower(Internship.source) == source.lower().strip()
                )
            if date_from:
                conditions.append(Internship.posted_date >= date_from)
            if date_to:
                conditions.append(Internship.posted_date <= date_to)

            if search:
                search_term = f"%{search.lower().strip()}%"
                conditions.append(
                    or_(
                        func.lower(Internship.title).like(search_term),
                        func.lower(Internship.company).like(search_term),
                        func.lower(Internship.skills).like(search_term),
                    )
                )

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Sorting
            if sort_by and hasattr(Internship, sort_by):
                col = getattr(Internship, sort_by)
                if order.lower() == "desc":
                    stmt = stmt.order_by(col.desc())
                else:
                    stmt = stmt.order_by(col.asc())
            else:
                stmt = stmt.order_by(Internship.id.asc())

            stmt = stmt.offset(skip).limit(limit)
            return list(session.scalars(stmt).all())

    def get_statistics(self) -> dict[str, Any]:
        """Gather database statistics for internships.

        Returns:
            Dictionary containing metrics: total, new_today, companies, sources breakdown.
        """
        from datetime import date
        from sqlalchemy import func, select

        from app.models.internship import Internship

        with self._repository() as repo:
            session = repo._session

            # 1. Total internships
            total = session.scalar(select(func.count(Internship.id))) or 0

            # 2. New today (created today)
            new_today = (
                session.scalar(
                    select(func.count(Internship.id)).where(
                        func.date(Internship.created_at) == date.today()
                    )
                )
                or 0
            )

            # 3. Unique companies
            unique_companies = (
                session.scalar(select(func.count(func.distinct(Internship.company))))
                or 0
            )

            # 4. Source breakdown
            sources_stmt = select(
                Internship.source, func.count(Internship.id)
            ).group_by(Internship.source)
            sources_res = session.execute(sources_stmt).all()
            sources_breakdown = {source: count for source, count in sources_res}

            return {
                "total": total,
                "new_today": new_today,
                "companies": unique_companies,
                "sources": sources_breakdown,
            }
