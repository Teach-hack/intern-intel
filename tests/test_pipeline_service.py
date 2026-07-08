"""Unit tests for PipelineService."""

from __future__ import annotations

from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DatabaseError, ScraperError
from app.models.internship import Internship
from app.services.database_service import DatabaseService
from app.services.dedup_service import DedupService
from app.services.mapper_service import MapperService
from app.services.pipeline_service import MapperError, PipelineService
from app.services.scraper_service import ScraperService


@pytest.fixture(name="mock_scraper_service")
def fixture_mock_scraper_service() -> MagicMock:
    """Create a mocked ScraperService."""
    return MagicMock(spec=ScraperService)


@pytest.fixture(name="mock_dedup_service")
def fixture_mock_dedup_service() -> MagicMock:
    """Create a mocked DedupService."""
    return MagicMock(spec=DedupService)


@pytest.fixture(name="mock_mapper_service")
def fixture_mock_mapper_service() -> MagicMock:
    """Create a mocked MapperService."""
    return MagicMock(spec=MapperService)


@pytest.fixture(name="mock_database_service")
def fixture_mock_database_service() -> MagicMock:
    """Create a mocked DatabaseService."""
    return MagicMock(spec=DatabaseService)


@pytest.fixture(name="mock_logger")
def fixture_mock_logger() -> Generator[MagicMock, None, None]:
    """Patch pipeline logger."""
    with patch("app.services.pipeline_service.logger") as mock:
        yield mock


@pytest.fixture(name="service")
def fixture_service(
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
) -> PipelineService:
    """Create PipelineService with mocked dependencies."""
    return PipelineService(
        scraper_service=mock_scraper_service,
        dedup_service=mock_dedup_service,
        mapper_service=mock_mapper_service,
        database_service=mock_database_service,
    )


def test_default_initialization() -> None:
    """Verify default dependency construction."""
    with patch("app.services.pipeline_service.http_client"):
        pipeline = PipelineService()

        assert isinstance(pipeline._scraper_service, ScraperService)
        assert isinstance(pipeline._dedup_service, DedupService)
        assert isinstance(pipeline._mapper_service, MapperService)
        assert isinstance(pipeline._database_service, DatabaseService)

        assert isinstance(
            pipeline._scraper_service,
            ScraperService,
        )


def test_dependency_injection(
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
) -> None:
    """Verify dependency injection."""
    pipeline = PipelineService(
        scraper_service=mock_scraper_service,
        dedup_service=mock_dedup_service,
        mapper_service=mock_mapper_service,
        database_service=mock_database_service,
    )

    assert pipeline._scraper_service is mock_scraper_service
    assert pipeline._dedup_service is mock_dedup_service
    assert pipeline._mapper_service is mock_mapper_service
    assert pipeline._database_service is mock_database_service


def test_run_success(
    service: PipelineService,
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify successful execution using default scrapers."""
    raw_jobs = [
        {
            "company": "Google",
            "title": "Intern",
            "url": "https://google.com",
        }
    ]

    internship = MagicMock(spec=Internship)

    mock_scraper_service.scrape_many.return_value = raw_jobs
    mock_dedup_service.deduplicate.return_value = raw_jobs
    mock_mapper_service.map_many.return_value = [internship]
    mock_database_service.save_many.return_value = [internship]

    from app.registry import CompanyRegistry
    from app.core.base_scraper import BaseScraper

    mock_registry = MagicMock(spec=CompanyRegistry)
    mock_registry.create_all.return_value = [MagicMock(spec=BaseScraper)]
    service._registry = mock_registry

    result = service.run()

    assert result == [internship]

    mock_scraper_service.scrape_many.assert_called_once()
    mock_dedup_service.deduplicate.assert_called_once_with(raw_jobs)
    mock_mapper_service.map_many.assert_called_once_with(raw_jobs)
    mock_database_service.save_many.assert_called_once_with([internship])

    mock_logger.info.assert_any_call("Pipeline started.")
    mock_logger.info.assert_any_call("Fetched {} raw jobs.", 1)
    mock_logger.info.assert_any_call(
        "{} unique jobs after deduplication.",
        1,
    )
    mock_logger.info.assert_any_call(
        "Mapped {} internship objects.",
        1,
    )
    mock_logger.info.assert_any_call(
        "Saved {} internship listings.",
        1,
    )
    mock_logger.info.assert_any_call(
        "Pipeline completed successfully.",
    )


def test_run_scrapers_success(
    service: PipelineService,
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
) -> None:
    """Verify successful execution with custom scrapers."""
    scraper = MagicMock()

    internship = MagicMock(spec=Internship)

    raw_jobs = [{"company": "Google"}]

    mock_scraper_service.scrape_many.return_value = raw_jobs
    mock_dedup_service.deduplicate.return_value = raw_jobs
    mock_mapper_service.map_many.return_value = [internship]
    mock_database_service.save_many.return_value = [internship]

    result = service.run_scrapers([scraper])

    assert result == [internship]

    mock_scraper_service.scrape_many.assert_called_once_with([scraper])
    mock_dedup_service.deduplicate.assert_called_once_with(raw_jobs)
    mock_mapper_service.map_many.assert_called_once_with(raw_jobs)
    mock_database_service.save_many.assert_called_once_with([internship])


@pytest.mark.parametrize(
    (
        "scraper_output",
        "dedup_output",
        "mapper_output",
        "expected",
    ),
    [
        ([], [], [], []),
        ([{"company": "Google"}], [], [], []),
        ([{"company": "Google"}], [{"company": "Google"}], [], []),
    ],
)
def test_pipeline_early_return(
    service: PipelineService,
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
    scraper_output: list,
    dedup_output: list,
    mapper_output: list,
    expected: list,
) -> None:
    """Verify pipeline exits early when intermediate stages return nothing."""
    mock_scraper_service.scrape_many.return_value = scraper_output
    mock_dedup_service.deduplicate.return_value = dedup_output
    mock_mapper_service.map_many.return_value = mapper_output

    result = service.run_scrapers([])

    assert result == expected

    mock_scraper_service.scrape_many.assert_called_once()

    if scraper_output:
        mock_dedup_service.deduplicate.assert_called_once()
    else:
        mock_dedup_service.deduplicate.assert_not_called()

    if dedup_output:
        mock_mapper_service.map_many.assert_called_once()
    else:
        mock_mapper_service.map_many.assert_not_called()

    mock_database_service.save_many.assert_not_called()


def test_database_save_empty(
    service: PipelineService,
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
) -> None:
    """Verify pipeline returns an empty list when database saves nothing."""
    internship = MagicMock(spec=Internship)

    mock_scraper_service.scrape_many.return_value = [{"company": "Google"}]
    mock_dedup_service.deduplicate.return_value = [{"company": "Google"}]
    mock_mapper_service.map_many.return_value = [internship]
    mock_database_service.save_many.return_value = []

    result = service.run_scrapers([])

    assert result == []

    mock_database_service.save_many.assert_called_once_with([internship])


@pytest.mark.parametrize(
    ("attribute", "exception"),
    [
        ("scrape_many", ScraperError("Scraper failed")),
        ("map_many", MapperError("Mapper failed")),
        ("save_many", DatabaseError("Database failed")),
    ],
)
def test_pipeline_known_exceptions(
    service: PipelineService,
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
    mock_logger: MagicMock,
    attribute: str,
    exception: Exception,
) -> None:
    """Verify application-specific exceptions are logged and re-raised."""
    mock_scraper_service.scrape_many.return_value = [{"company": "Google"}]
    mock_dedup_service.deduplicate.return_value = [{"company": "Google"}]
    mock_mapper_service.map_many.return_value = [MagicMock(spec=Internship)]

    if attribute == "scrape_many":
        mock_scraper_service.scrape_many.side_effect = exception

    elif attribute == "map_many":
        mock_mapper_service.map_many.side_effect = exception

    else:
        mock_database_service.save_many.side_effect = exception

    with pytest.raises(type(exception)):
        service.run_scrapers([])

    mock_logger.exception.assert_called_once_with(
        "Pipeline execution failed: {}",
        exception,
    )


def test_generic_exception_propagation(
    mock_scraper_service: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Verify unexpected exceptions propagate without pipeline logging."""
    service = PipelineService(
        scraper_service=mock_scraper_service,
    )

    mock_scraper_service.scrape_many.side_effect = RuntimeError("Unexpected failure")

    with pytest.raises(
        RuntimeError,
        match="Unexpected failure",
    ):
        service.run_scrapers([])

    mock_logger.exception.assert_not_called()


def test_execution_order(
    service: PipelineService,
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
) -> None:
    """Verify pipeline stages execute in the expected order."""
    calls: list[str] = []

    internship = MagicMock(spec=Internship)

    def scrape(_: list) -> list:
        calls.append("scrape")
        return [{"company": "Google"}]

    def dedup(jobs: list) -> list:
        calls.append("dedup")
        return jobs

    def mapper(jobs: list) -> list:
        calls.append("map")
        return [internship]

    def save(jobs: list) -> list:
        calls.append("save")
        return jobs

    mock_scraper_service.scrape_many.side_effect = scrape
    mock_dedup_service.deduplicate.side_effect = dedup
    mock_mapper_service.map_many.side_effect = mapper
    mock_database_service.save_many.side_effect = save

    result = service.run_scrapers([])

    assert result == [internship]
    assert calls == [
        "scrape",
        "dedup",
        "map",
        "save",
    ]


def test_run_uses_default_scrapers(
    service: PipelineService,
) -> None:
    """Verify run() delegates to run_scrapers()."""
    expected = [MagicMock(spec=Internship)]

    with (
        patch.object(
            PipelineService,
            "_create_default_scrapers",
            return_value=[],
        ) as mock_factory,
        patch.object(
            PipelineService,
            "run_scrapers",
            return_value=expected,
        ) as mock_runner,
    ):
        result = service.run()

    assert result == expected
    mock_factory.assert_called_once()
    mock_runner.assert_called_once_with([])


def test_pipeline_returns_saved_jobs(
    service: PipelineService,
    mock_scraper_service: MagicMock,
    mock_dedup_service: MagicMock,
    mock_mapper_service: MagicMock,
    mock_database_service: MagicMock,
) -> None:
    """Verify saved ORM objects are returned unchanged."""
    internship = MagicMock(spec=Internship)

    mock_scraper_service.scrape_many.return_value = [{"company": "Google"}]
    mock_dedup_service.deduplicate.return_value = [{"company": "Google"}]
    mock_mapper_service.map_many.return_value = [internship]
    mock_database_service.save_many.return_value = [internship]

    result = service.run_scrapers([])

    assert result is mock_database_service.save_many.return_value


def test_create_default_scrapers() -> None:
    pipeline = PipelineService()

    scrapers = pipeline._create_default_scrapers()

    assert len(scrapers) == 2

    assert isinstance(
        scrapers[0],
        GreenhouseScraper,
    )

    assert isinstance(
        scrapers[1],
        LeverScraper,
    )
