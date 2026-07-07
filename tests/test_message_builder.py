"""Unit tests for the MessageBuilder class."""

from __future__ import annotations

import datetime

from app.models.internship import Internship
from app.notifications.message_builder import MessageBuilder


def test_build_all_fields() -> None:
    """Verify formatting when all optional fields are present."""
    job = Internship(
        company="Google",
        title="SWE Intern",
        location="Remote",
        employment_type="internship",
        work_mode="remote",
        url="https://google.com/jobs/123",
        posted_date=datetime.date(2026, 7, 7),
        source="google",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build(job)
    expected = (
        "🚀 New Internship\n\n"
        "Company: Google\n\n"
        "Title: SWE Intern\n\n"
        "Location: Remote\n\n"
        "Type: Internship\n\n"
        "Posted: 2026-07-07\n\n"
        "Apply:\n"
        "https://google.com/jobs/123"
    )
    assert message == expected


def test_build_missing_location() -> None:
    """Verify that location line is omitted if location is missing."""
    job = Internship(
        company="Google",
        title="SWE Intern",
        location=None,
        employment_type="internship",
        work_mode="remote",
        url="https://google.com/jobs/123",
        posted_date=datetime.date(2026, 7, 7),
        source="google",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build(job)
    expected = (
        "🚀 New Internship\n\n"
        "Company: Google\n\n"
        "Title: SWE Intern\n\n"
        "Type: Internship\n\n"
        "Posted: 2026-07-07\n\n"
        "Apply:\n"
        "https://google.com/jobs/123"
    )
    assert message == expected


def test_build_missing_posted_date() -> None:
    """Verify that posted line is omitted if posted_date is missing."""
    job = Internship(
        company="Google",
        title="SWE Intern",
        location="Remote",
        employment_type="internship",
        work_mode="remote",
        url="https://google.com/jobs/123",
        posted_date=None,
        source="google",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build(job)
    expected = (
        "🚀 New Internship\n\n"
        "Company: Google\n\n"
        "Title: SWE Intern\n\n"
        "Location: Remote\n\n"
        "Type: Internship\n\n"
        "Apply:\n"
        "https://google.com/jobs/123"
    )
    assert message == expected


def test_build_missing_both() -> None:
    """Verify that both location and posted lines are omitted if both are missing."""
    job = Internship(
        company="Google",
        title="SWE Intern",
        location=None,
        employment_type="internship",
        work_mode="remote",
        url="https://google.com/jobs/123",
        posted_date=None,
        source="google",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build(job)
    expected = (
        "🚀 New Internship\n\n"
        "Company: Google\n\n"
        "Title: SWE Intern\n\n"
        "Type: Internship\n\n"
        "Apply:\n"
        "https://google.com/jobs/123"
    )
    assert message == expected


def test_build_many() -> None:
    """Verify that multiple jobs are correctly separated by the divider."""
    job1 = Internship(
        company="Google",
        title="SWE Intern",
        location="Remote",
        employment_type="internship",
        work_mode="remote",
        url="https://google.com/jobs/1",
        posted_date=datetime.date(2026, 7, 7),
        source="google",
        status="new",
    )
    job2 = Internship(
        company="Meta",
        title="Production Engineer Intern",
        location="New York",
        employment_type="internship",
        work_mode="hybrid",
        url="https://meta.com/jobs/2",
        posted_date=None,
        source="meta",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build_many([job1, job2])
    expected = (
        "🚀 New Internship\n\n"
        "Company: Google\n\n"
        "Title: SWE Intern\n\n"
        "Location: Remote\n\n"
        "Type: Internship\n\n"
        "Posted: 2026-07-07\n\n"
        "Apply:\n"
        "https://google.com/jobs/1\n\n"
        "---------------------\n\n"
        "🚀 New Internship\n\n"
        "Company: Meta\n\n"
        "Title: Production Engineer Intern\n\n"
        "Location: New York\n\n"
        "Type: Internship\n\n"
        "Apply:\n"
        "https://meta.com/jobs/2"
    )
    assert message == expected


def test_build_many_empty() -> None:
    """Verify that build_many with empty list returns empty string."""
    builder = MessageBuilder()
    assert builder.build_many([]) == ""


def test_truncate_safely() -> None:
    """Verify that very long messages are truncated to <= 4000 characters."""
    long_company_name = "Google" + "o" * 4000
    job = Internship(
        company=long_company_name,
        title="SWE Intern",
        location="Remote",
        employment_type="internship",
        work_mode="remote",
        url="https://google.com/jobs/123",
        posted_date=datetime.date(2026, 7, 7),
        source="google",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build(job)
    assert len(message) <= 4000
    assert message.endswith("...")


def test_truncate_word_boundary() -> None:
    """Verify that truncation respects word/whitespace boundaries if within lookback."""
    # We want a message where the length exceeds 4000, and a space is near the limit.
    # Base message has about 120 chars. We insert a long word.
    builder = MessageBuilder()

    # We will test the _truncate helper directly with customized input
    # Limit is 4000, max_length - 3 is 3997.
    # Let's construct a string where there is a space at index 3990.
    test_str = "A" * 3990 + " BBBB" + "C" * 15
    truncated = builder._truncate(test_str, max_length=4000)

    assert len(truncated) <= 4000
    assert truncated.endswith("...")
    # The trailing "BBBB" and "CCCC" should be truncated, splitting at the space
    assert truncated == "A" * 3990 + "..."


def test_unicode_and_markdown_characters() -> None:
    """Verify that unicode characters and markdown syntax inside fields format correctly."""
    job = Internship(
        company="グーグル (Google™) 🚀",
        title="*SWE* **Intern** `2026`",
        location="Remote [World]",
        employment_type="internship",
        work_mode="remote",
        url="https://google.com/jobs/123",
        posted_date=datetime.date(2026, 7, 7),
        source="google",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build(job)
    expected = (
        "🚀 New Internship\n\n"
        "Company: グーグル (Google™) 🚀\n\n"
        "Title: *SWE* **Intern** `2026`\n\n"
        "Location: Remote [World]\n\n"
        "Type: Internship\n\n"
        "Posted: 2026-07-07\n\n"
        "Apply:\n"
        "https://google.com/jobs/123"
    )
    assert message == expected


def test_build_many_ordering() -> None:
    """Verify that build_many preserves the input ordering of the internships."""
    job_first = Internship(
        company="Company A",
        title="First Job",
        location="Location A",
        employment_type="internship",
        work_mode="remote",
        url="https://a.com",
        posted_date=datetime.date(2026, 7, 1),
        source="source_a",
        status="new",
    )
    job_second = Internship(
        company="Company B",
        title="Second Job",
        location="Location B",
        employment_type="internship",
        work_mode="remote",
        url="https://b.com",
        posted_date=datetime.date(2026, 7, 2),
        source="source_b",
        status="new",
    )
    builder = MessageBuilder()
    message = builder.build_many([job_first, job_second])

    # Assert that the text of the first job appears before the text of the second job
    index_first = message.index("Company: Company A")
    index_second = message.index("Company: Company B")
    assert index_first < index_second
