"""Unit tests for the DedupService."""

from __future__ import annotations

from typing import Any

from app.services.dedup_service import DedupService


def test_empty_list() -> None:
    """Verify that deduplicate handles an empty list correctly."""
    service = DedupService()
    assert service.deduplicate([]) == []


def test_single_job() -> None:
    """Verify that a single job listing is returned correctly."""
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
    assert results[0]["company"] == "Google"
    assert results[0]["url"] == "https://careers.google.com/1"


def test_deduplicate_by_exact_url() -> None:
    """Verify that jobs with duplicate URLs are removed, preserving the first."""
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
            "url": "https://careers.google.com/1",  # Duplicate URL
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
    """Verify that jobs with duplicate company + title (case-insensitive) are removed."""
    service = DedupService()
    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        },
        {
            "company": " google ",  # case-insensitive and whitespace duplicate
            "title": "  Software Engineer  ",
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


def test_different_companies() -> None:
    """Verify that same title at different companies is not deduplicated."""
    service = DedupService()
    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        },
        {
            "company": "Meta",
            "title": "Software Engineer",
            "url": "https://careers.meta.com/2",
        },
    ]
    results = service.deduplicate(jobs)
    assert len(results) == 2
    assert results[0]["company"] == "Google"
    assert results[1]["company"] == "Meta"


def test_different_titles() -> None:
    """Verify that different titles at the same company are not deduplicated."""
    service = DedupService()
    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        },
        {
            "company": "Google",
            "title": "Product Manager",
            "url": "https://careers.google.com/2",
        },
    ]
    results = service.deduplicate(jobs)
    assert len(results) == 2
    assert results[0]["title"] == "Software Engineer"
    assert results[1]["title"] == "Product Manager"


def test_preserve_first_occurrence() -> None:
    """Verify that the first occurrence of a duplicate group is preserved."""
    service = DedupService()
    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/first",
            "stipend": "$5000",
        },
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/second",
            "stipend": "$6000",
        },
    ]
    results = service.deduplicate(jobs)
    assert len(results) == 1
    assert results[0]["url"] == "https://careers.google.com/first"
    assert results[0]["stipend"] == "$5000"


def test_no_mutation() -> None:
    """Verify that the input list and its dictionaries are not mutated."""
    service = DedupService()
    jobs = [
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        }
    ]

    # Create a deep copy of the original state to verify no mutations occur
    original_jobs = [job.copy() for job in jobs]

    results = service.deduplicate(jobs)

    # Change the output to verify shallow copy was returned and didn't affect input
    results[0]["company"] = "Meta"

    assert jobs == original_jobs
    assert jobs[0]["company"] == "Google"


def test_ignore_missing_keys() -> None:
    """Verify that jobs missing required keys are ignored."""
    service = DedupService()
    jobs = [
        # Valid
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        },
        # Missing company
        {
            "title": "Software Engineer",
            "url": "https://careers.google.com/2",
        },
        # Missing title
        {
            "company": "Google",
            "url": "https://careers.google.com/3",
        },
        # Missing url
        {
            "company": "Google",
            "title": "Software Engineer",
        },
    ]

    results = service.deduplicate(jobs)
    assert len(results) == 1
    assert results[0]["url"] == "https://careers.google.com/1"


def test_ignore_invalid_types() -> None:
    """Verify that jobs with invalid types or non-dictionary entries are ignored."""
    service = DedupService()
    jobs: list[Any] = [
        "not a dictionary",
        None,
        {
            "company": 123,  # Invalid type
            "title": "Software Engineer",
            "url": "https://careers.google.com/1",
        },
        {
            "company": "Google",
            "title": None,  # Invalid type
            "url": "https://careers.google.com/1",
        },
        {
            "company": "Google",
            "title": "Software Engineer",
            "url": "",  # Empty string
        },
    ]

    results = service.deduplicate(jobs)
    assert len(results) == 0
