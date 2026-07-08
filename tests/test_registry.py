"""Unit tests for the CompanyRegistry class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.base_scraper import BaseScraper
from app.registry import CompanyRegistry, create_default_registry


@pytest.fixture
def mock_scraper() -> MagicMock:
    """Fixture to construct a mocked scraper instance."""
    return MagicMock(spec=BaseScraper)


def test_registry_initialization() -> None:
    """Verify that CompanyRegistry initializes empty."""
    registry = CompanyRegistry()
    assert registry.list_names() == []


def test_registry_register_and_get(mock_scraper: MagicMock) -> None:
    """Verify standard register and get functionality."""
    registry = CompanyRegistry()

    def factory() -> BaseScraper:
        return mock_scraper

    with patch("app.registry.logger") as mock_logger:
        registry.register("test_scraper", factory)

    mock_logger.info.assert_called_once_with(
        "Registered scraper factory for name: '{}'", "test_scraper"
    )
    assert registry.get("test_scraper") is factory
    assert registry.exists("test_scraper")
    assert registry.list_names() == ["test_scraper"]


def test_registry_register_invalid_names(mock_scraper: MagicMock) -> None:
    """Verify that empty/whitespace names raise ValueError."""
    registry = CompanyRegistry()

    def factory() -> BaseScraper:
        return mock_scraper

    with pytest.raises(ValueError, match="Scraper name must not be empty"):
        registry.register("", factory)

    with pytest.raises(ValueError, match="Scraper name must not be empty"):
        registry.register("   ", factory)


def test_registry_duplicate_registration(mock_scraper: MagicMock) -> None:
    """Verify that duplicate registrations raise ValueError."""
    registry = CompanyRegistry()

    def factory() -> BaseScraper:
        return mock_scraper

    registry.register("test_scraper", factory)
    with pytest.raises(ValueError, match="Scraper already registered: test_scraper"):
        registry.register("test_scraper", factory)


def test_registry_get_unregistered() -> None:
    """Verify that getting an unregistered name raises ValueError."""
    registry = CompanyRegistry()
    with pytest.raises(ValueError, match="Scraper not registered: missing"):
        registry.get("missing")


def test_registry_create(mock_scraper: MagicMock) -> None:
    """Verify lazy creation via scraper factory invocation."""
    registry = CompanyRegistry()
    factory_calls = 0

    def mock_factory() -> BaseScraper:
        nonlocal factory_calls
        factory_calls += 1
        return mock_scraper

    registry.register("test_scraper", mock_factory)
    assert factory_calls == 0  # Lazy construction check

    scraper_instance = registry.create("test_scraper")
    assert scraper_instance is mock_scraper
    assert factory_calls == 1


def test_registry_create_all(mock_scraper: MagicMock) -> None:
    """Verify create_all correctly constructs all registered scrapers."""
    registry = CompanyRegistry()
    mock_scraper_2 = MagicMock(spec=BaseScraper)

    registry.register("first", lambda: mock_scraper)
    registry.register("second", lambda: mock_scraper_2)

    scrapers = registry.create_all()
    assert scrapers == [mock_scraper, mock_scraper_2]


def test_registry_clear(mock_scraper: MagicMock) -> None:
    """Verify that clearing the registry removes all registrations."""
    registry = CompanyRegistry()
    registry.register("test_scraper", lambda: mock_scraper)
    assert registry.exists("test_scraper")

    with patch("app.registry.logger") as mock_logger:
        registry.clear()

    mock_logger.info.assert_called_once_with(
        "Cleared all registered scraper factories."
    )
    assert not registry.exists("test_scraper")
    assert registry.list_names() == []


def test_registry_ordering(mock_scraper: MagicMock) -> None:
    """Verify that registry preserves the order of scraper registrations."""
    registry = CompanyRegistry()
    registry.register("c", lambda: mock_scraper)
    registry.register("a", lambda: mock_scraper)
    registry.register("b", lambda: mock_scraper)

    assert registry.list_names() == ["c", "a", "b"]


def test_create_default_registry() -> None:
    """Verify create_default_registry pre-populates default scrapers."""
    # Patch settings to ensure loading constants
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.get.side_effect = lambda key, default=None: {
            "scrapers.greenhouse.board_token": "board1",
            "scrapers.lever.site_slug": "slug1",
        }.get(key, default)

        registry = create_default_registry()
        assert registry.list_names() == ["greenhouse", "lever"]

        greenhouse = registry.create("greenhouse")
        lever = registry.create("lever")

        assert greenhouse.get_source_name() == "greenhouse"
        assert lever.get_source_name() == "lever"
