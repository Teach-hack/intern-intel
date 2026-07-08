"""Unit tests for the InternshipRepository."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.repository import InternshipRepository
from app.models.internship import Internship


from pathlib import Path
from app.core.settings import Settings
from app.database.migrations import MigrationService


@pytest.fixture(name="db_session")
def fixture_db_session(tmp_path: Path) -> Generator[Session, None, None]:
    """Provide an isolated database session using Alembic migrations."""
    db_path = tmp_path / "test_repo.db"
    settings = Settings(
        {"database": {"path": str(db_path), "url": f"sqlite:///{db_path}"}}
    )

    # Run migrations to build the schema
    ms = MigrationService(settings=settings)
    ms.upgrade("head")

    engine = create_engine(settings.database_url, future=True)
    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def make_job(
    *,
    company: str = "Google",
    title: str = "Software Engineer Intern",
    url: str = "https://careers.google.com/1",
    work_mode: str = "remote",
    source: str = "google",
) -> Internship:
    """Create a reusable Internship instance for testing."""
    return Internship(
        company=company,
        title=title,
        url=url,
        employment_type="internship",
        work_mode=work_mode,
        source=source,
        status="new",
    )


def test_repository_initially_empty(db_session: Session) -> None:
    """Verify a fresh repository contains no records."""
    repo = InternshipRepository(db_session)

    assert repo.count() == 0
    assert repo.get_all() == []


def test_add(db_session: Session) -> None:
    """Verify a single Internship can be added."""
    repo = InternshipRepository(db_session)

    job = make_job()

    result = repo.add(job)

    assert result.id is not None
    assert repo.count() == 1
    assert result.company == "Google"


def test_add_many(db_session: Session) -> None:
    """Verify multiple Internship records can be added."""
    repo = InternshipRepository(db_session)

    jobs = [
        make_job(),
        make_job(
            company="Meta",
            title="PE Intern",
            url="https://careers.meta.com/1",
            source="meta",
            work_mode="hybrid",
        ),
    ]

    result = repo.add_many(jobs)

    assert len(result) == 2
    assert result[0].id is not None
    assert result[1].id is not None
    assert repo.count() == 2


def test_add_many_empty(db_session: Session) -> None:
    """Verify add_many handles an empty list."""
    repo = InternshipRepository(db_session)

    result = repo.add_many([])

    assert result == []
    assert repo.count() == 0


def test_get_by_url(db_session: Session) -> None:
    """Verify lookup by URL."""
    repo = InternshipRepository(db_session)

    url = "https://careers.google.com/1"

    assert repo.get_by_url(url) is None

    repo.add(make_job(url=url))

    job = repo.get_by_url(url)

    assert job is not None
    assert job.url == url
    assert job.company == "Google"


def test_get_by_company_and_title(db_session: Session) -> None:
    """Verify lookup by company and title."""
    repo = InternshipRepository(db_session)

    repo.add(make_job())

    job = repo.get_by_company_and_title(
        "Google",
        "Software Engineer Intern",
    )

    assert job is not None
    assert job.url == "https://careers.google.com/1"

    assert (
        repo.get_by_company_and_title(
            "Meta",
            "Software Engineer Intern",
        )
        is None
    )

    assert (
        repo.get_by_company_and_title(
            "Google",
            "Backend Intern",
        )
        is None
    )


def test_get_all(db_session: Session) -> None:
    """Verify retrieval of all stored jobs."""
    repo = InternshipRepository(db_session)

    repo.add_many(
        [
            make_job(),
            make_job(
                company="Meta",
                title="PE Intern",
                url="https://careers.meta.com/1",
                source="meta",
            ),
        ]
    )

    jobs = repo.get_all()

    assert len(jobs) == 2

    companies = {job.company for job in jobs}

    assert companies == {"Google", "Meta"}


def test_exists(db_session: Session) -> None:
    """Verify exists returns correct values."""
    repo = InternshipRepository(db_session)

    url = "https://careers.google.com/1"

    assert not repo.exists(url)

    repo.add(make_job(url=url))

    assert repo.exists(url)


def test_exists_unknown_url(db_session: Session) -> None:
    """Verify exists returns False for unknown URLs."""
    repo = InternshipRepository(db_session)

    assert not repo.exists("https://example.com/unknown")


def test_count(db_session: Session) -> None:
    """Verify count returns the correct number of rows."""
    repo = InternshipRepository(db_session)

    assert repo.count() == 0

    repo.add(make_job())

    assert repo.count() == 1

    repo.add(
        make_job(
            company="Meta",
            title="PE Intern",
            url="https://careers.meta.com/1",
            source="meta",
        )
    )

    assert repo.count() == 2


def test_delete(db_session: Session) -> None:
    """Verify deletion of a single record."""
    repo = InternshipRepository(db_session)

    job = make_job()

    repo.add(job)

    assert repo.count() == 1

    repo.delete(job)

    assert repo.count() == 0
    assert repo.get_by_url(job.url) is None


def test_exists_after_delete(db_session: Session) -> None:
    """Verify exists becomes False after deletion."""
    repo = InternshipRepository(db_session)

    job = make_job()

    repo.add(job)

    assert repo.exists(job.url)

    repo.delete(job)

    assert not repo.exists(job.url)


def test_delete_all(db_session: Session) -> None:
    """Verify delete_all removes every record."""
    repo = InternshipRepository(db_session)

    repo.add_many(
        [
            make_job(),
            make_job(
                company="Meta",
                title="PE Intern",
                url="https://careers.meta.com/1",
                source="meta",
            ),
        ]
    )

    assert repo.count() == 2

    deleted = repo.delete_all()

    assert deleted == 2
    assert repo.count() == 0
    assert repo.get_all() == []


def test_delete_all_empty(db_session: Session) -> None:
    """Verify delete_all on an empty repository."""
    repo = InternshipRepository(db_session)

    deleted = repo.delete_all()

    assert deleted == 0
    assert repo.count() == 0


def test_get_all_preserves_insert_order(db_session: Session) -> None:
    """Verify get_all preserves insertion order."""
    repo = InternshipRepository(db_session)

    first = make_job(
        title="First",
        url="https://google.com/1",
    )

    second = make_job(
        company="Meta",
        title="Second",
        url="https://meta.com/2",
        source="meta",
    )

    repo.add_many([first, second])

    jobs = repo.get_all()

    assert len(jobs) == 2
    assert jobs[0].title == "First"
    assert jobs[1].title == "Second"
