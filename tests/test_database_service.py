"""Unit tests for the DatabaseService."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from app.models.internship import Internship
from app.services.database_service import DatabaseService


@pytest.fixture(name="mock_session")
def fixture_mock_session() -> MagicMock:
    """Return a mocked SQLAlchemy session."""
    return MagicMock()


@pytest.fixture(name="mock_get_session")
def fixture_mock_get_session(
    mock_session: MagicMock,
) -> Generator[MagicMock, None, None]:
    """Mock get_session()."""
    with patch("app.services.database_service.get_session") as mock:
        mock.return_value.__enter__.return_value = mock_session
        yield mock


@pytest.fixture(name="mock_repo")
def fixture_mock_repo() -> Generator[MagicMock, None, None]:
    """Mock InternshipRepository."""
    with patch("app.services.database_service.InternshipRepository") as mock:
        yield mock


@pytest.fixture(name="mock_logger")
def fixture_mock_logger() -> Generator[MagicMock, None, None]:
    """Mock logger."""
    with patch("app.services.database_service.logger") as mock:
        yield mock


def test_service_initialization() -> None:
    """Verify DatabaseService initializes."""
    service = DatabaseService()

    assert isinstance(service, DatabaseService)


def test_save(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_session: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify save()."""
    service = DatabaseService()

    job = MagicMock(spec=Internship)
    job.company = "Google"
    job.title = "Intern"
    job.url = "https://google.com/1"

    repo = mock_repo.return_value
    repo.add.return_value = job

    result = service.save(job)

    mock_get_session.assert_called_once()
    mock_repo.assert_called_once_with(mock_session)
    repo.add.assert_called_once_with(job)

    mock_logger.info.assert_called_once_with(
        "Saved internship | company={} | title={} | url={}",
        job.company,
        job.title,
        job.url,
    )

    assert result is job


def test_save_none() -> None:
    """Verify save(None) raises."""
    service = DatabaseService()

    with pytest.raises(ValueError, match="job must not be None"):
        service.save(None)  # type: ignore[arg-type]


def test_save_many(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_session: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify save_many()."""
    service = DatabaseService()

    jobs: list[Internship] = [
        MagicMock(spec=Internship),
        MagicMock(spec=Internship),
    ]  # type: ignore[list-item]

    repo = mock_repo.return_value
    repo.add_many.return_value = jobs

    result = service.save_many(jobs)

    mock_get_session.assert_called_once()
    mock_repo.assert_called_once_with(mock_session)
    repo.add_many.assert_called_once_with(jobs)

    mock_logger.info.assert_called_once_with(
        "Saved {} internship listings.",
        2,
    )

    assert result == jobs


def test_save_many_empty(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify empty save_many()."""
    service = DatabaseService()

    assert service.save_many([]) == []

    mock_get_session.assert_not_called()
    mock_repo.assert_not_called()

    mock_logger.debug.assert_called_once_with(
        "No internship listings supplied for bulk save."
    )


def test_exists(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_session: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify exists()."""
    service = DatabaseService()

    repo = mock_repo.return_value
    repo.exists.return_value = True

    url = "https://google.com/1"

    result = service.exists(url)

    assert result is True

    repo.exists.assert_called_once_with(url)

    mock_logger.debug.assert_called_once_with(
        "Checked existence for '{}': {}",
        url,
        True,
    )


def test_exists_empty_url() -> None:
    """Verify blank URL raises."""
    service = DatabaseService()

    with pytest.raises(ValueError, match="url must not be empty"):
        service.exists(" ")


def test_get_all(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_session: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify get_all()."""
    service = DatabaseService()

    jobs = [
        MagicMock(spec=Internship),
        MagicMock(spec=Internship),
    ]

    repo = mock_repo.return_value
    repo.get_all.return_value = jobs

    result = service.get_all()

    assert result == jobs

    repo.get_all.assert_called_once()

    mock_logger.info.assert_called_once_with(
        "Retrieved {} internship listings.",
        2,
    )


def test_count(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_session: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify count()."""
    service = DatabaseService()

    repo = mock_repo.return_value
    repo.count.return_value = 10

    assert service.count() == 10

    repo.count.assert_called_once()

    mock_logger.debug.assert_called_once_with(
        "Current internship count: {}",
        10,
    )


def test_delete(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_session: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify delete()."""
    service = DatabaseService()

    job = MagicMock(spec=Internship)
    job.company = "Google"
    job.title = "Intern"
    job.url = "https://google.com/1"

    repo = mock_repo.return_value

    service.delete(job)

    repo.delete.assert_called_once_with(job)

    mock_logger.info.assert_called_once_with(
        "Deleted internship | company={} | title={} | url={}",
        job.company,
        job.title,
        job.url,
    )


def test_delete_none() -> None:
    """Verify delete(None)."""
    service = DatabaseService()

    with pytest.raises(ValueError, match="job must not be None"):
        service.delete(None)  # type: ignore[arg-type]


def test_delete_all(
    mock_get_session: MagicMock,
    mock_repo: MagicMock,
    mock_session: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify delete_all()."""
    service = DatabaseService()

    repo = mock_repo.return_value
    repo.delete_all.return_value = 5

    assert service.delete_all() == 5

    repo.delete_all.assert_called_once()

    mock_logger.info.assert_called_once_with(
        "Deleted {} internship listings.",
        5,
    )
