"""Unit tests for the DedupService."""

from __future__ import annotations

from typing import Any

from app.services.dedup_service import DedupService


def test_empty_list() -> None:
    """Verify that an empty input returns an empty list."""
    service = DedupService()

    assert service.deduplicate([]) == []


def test_single_job() -> None:
    """Verify that a single job is returned unchanged."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        }
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 1
    assert results[0] == jobs[0]
    assert results[0] is not jobs[0]


def test_deduplicate_by_exact_url() -> None:
    """Verify duplicate URLs are removed."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        },
        {
            "company": "Alphabet",
            "title": "SWE",
            "url": "https://careers.google.com/1",
        },
        {
            "company": "Meta",
            "title": "Data Scientist",
            "url": "https://careers.meta.com/2",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 2
    assert results[0]["company"] == "Google"
    assert results[1]["company"] == "Meta"


def test_deduplicate_by_company_and_title() -> None:
    """Verify duplicate company/title pairs are removed."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        },
        {
            "company": " google ",
            "title": "  Software Engineer ",
            "url": "https://careers.google.com/2",
        },
        {
            "company": "Google",
            "title": "Product Manager",
            "url": "https://careers.google.com/3",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 2
    assert results[0]["url"] == "https://careers.google.com/1"
    assert results[1]["url"] == "https://careers.google.com/3"


def test_casefold_matching() -> None:
    """Verify Unicode-aware case-insensitive matching."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Intern",
            "url": "https://a.com",
        },
        {
            "company": "GOOGLE",
            "title": "intern",
            "url": "https://b.com",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 1


def test_different_companies() -> None:
    """Verify same title at different companies is preserved."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://google.com/1",
        },
        {
            "company": "Meta",
            "title": "Software Engineer",
            "url": "https://meta.com/1",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 2


def test_different_titles() -> None:
    """Verify different titles at same company are preserved."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Backend Engineer",
            "url": "https://google.com/1",
        },
        {
            "company": "Google",
            "title": "Frontend Engineer",
            "url": "https://google.com/2",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 2


def test_preserve_first_occurrence() -> None:
    """Verify first duplicate is preserved."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Intern",
            "url": "https://google.com/1",
            "stipend": "$5000",
        },
        {
            "company": "Google",
            "title": "Intern",
            "url": "https://google.com/2",
            "stipend": "$6000",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 1
    assert results[0]["stipend"] == "$5000"


def test_no_mutation() -> None:
    """Verify returned jobs are copies."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Intern",
            "url": "https://google.com/1",
        }
    ]

    original = [job.copy() for job in jobs]

    results = service.deduplicate(jobs)

    results[0]["company"] = "Meta"

    assert jobs == original
    assert jobs[0]["company"] == "Google"


def test_ignore_missing_keys() -> None:
    """Verify malformed records are ignored."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Intern",
            "url": "https://google.com/1",
        },
        {
            "title": "Intern",
            "url": "https://google.com/2",
        },
        {
            "company": "Google",
            "url": "https://google.com/3",
        },
        {
            "company": "Google",
            "title": "Intern",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 1


def test_ignore_invalid_types() -> None:
    """Verify invalid records are ignored."""
    service = DedupService()

    jobs: list[Any] = [
        "invalid",
        None,
        123,
        [],
        {
            "company": 123,
            "title": "Intern",
            "url": "https://google.com/1",
        },
        {
            "company": "Google",
            "title": None,
            "url": "https://google.com/2",
        },
        {
            "company": "Google",
            "title": "Intern",
            "url": "",
        },
    ]

    assert service.deduplicate(jobs) == []


def test_whitespace_values_are_ignored() -> None:
    """Verify blank string values are ignored."""
    service = DedupService()

    jobs = [
        {
            "company": "   ",
            "title": "Intern",
            "url": "https://google.com/1",
        },
        {
            "company": "Google",
            "title": "   ",
            "url": "https://google.com/2",
        },
        {
            "company": "Google",
            "title": "Intern",
            "url": "   ",
        },
    ]

    assert service.deduplicate(jobs) == []


def test_preserve_order() -> None:
    """Verify original ordering is preserved."""
    service = DedupService()

    jobs = [
        {
            "company": "A",
            "title": "One",
            "url": "https://a.com",
        },
        {
            "company": "B",
            "title": "Two",
            "url": "https://b.com",
        },
        {
            "company": "A",
            "title": "One",
            "url": "https://c.com",
        },
    ]

    results = service.deduplicate(jobs)

    assert [job["company"] for job in results] == ["A", "B"]


def test_url_has_priority_over_company_title() -> None:
    """Verify duplicate URL wins before company/title comparison."""
    service = DedupService()

    jobs = [
        {
            "company": "Google",
            "title": "Intern",
            "url": "https://same.com",
        },
        {
            "company": "Meta",
            "title": "Research",
            "url": "https://same.com",
        },
    ]

    results = service.deduplicate(jobs)

    assert len(results) == 1
    assert results[0]["company"] == "Google"
