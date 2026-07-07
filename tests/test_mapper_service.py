"""Unit tests for MapperService."""

from __future__ import annotations

from datetime import date

from app.models.internship import Internship
from app.services.mapper_service import MapperService


def test_map_complete_job() -> None:
    """Verify complete mapping."""

    service = MapperService()

    job = {
        "company": "Google",
        "title": "Software Engineer Intern",
        "location": "Remote",
        "employment_type": "internship",
        "work_mode": "remote",
        "url": "https://google.com/job",
        "posted_date": date(2026, 1, 1),
        "deadline": date(2026, 2, 1),
        "stipend": "$5000",
        "skills": "Python",
        "source": "google",
        "status": "new",
    }

    internship = service.map(job)

    assert isinstance(internship, Internship)
    assert internship.company == "Google"
    assert internship.title == "Software Engineer Intern"
    assert internship.location == "Remote"
    assert internship.employment_type == "internship"
    assert internship.work_mode == "remote"
    assert internship.url == "https://google.com/job"
    assert internship.posted_date == date(2026, 1, 1)
    assert internship.deadline == date(2026, 2, 1)
    assert internship.stipend == "$5000"
    assert internship.skills == "Python"
    assert internship.source == "google"
    assert internship.status == "new"


def test_default_status() -> None:
    """Verify default status."""

    service = MapperService()

    internship = service.map(
        {
            "company": "Google",
            "title": "Intern",
            "employment_type": "internship",
            "work_mode": "remote",
            "url": "https://google.com/job",
            "source": "google",
        }
    )

    assert internship.status == "new"


def test_optional_fields_none() -> None:
    """Verify optional fields."""

    service = MapperService()

    internship = service.map(
        {
            "company": "Google",
            "title": "Intern",
            "employment_type": "internship",
            "work_mode": "remote",
            "url": "https://google.com/job",
            "location": None,
            "posted_date": None,
            "deadline": None,
            "stipend": None,
            "skills": None,
            "source": "google",
        }
    )

    assert internship.location is None
    assert internship.posted_date is None
    assert internship.deadline is None
    assert internship.stipend is None
    assert internship.skills is None


def test_optional_string_cleanup() -> None:
    """Verify whitespace-only strings become None."""

    service = MapperService()

    internship = service.map(
        {
            "company": "Google",
            "title": "Intern",
            "employment_type": "internship",
            "work_mode": "remote",
            "url": "https://google.com/job",
            "location": "   ",
            "stipend": "",
            "skills": " ",
            "source": "google",
        }
    )

    assert internship.location is None
    assert internship.stipend is None
    assert internship.skills is None


def test_map_many() -> None:
    """Verify batch mapping."""

    service = MapperService()

    jobs = [
        {
            "company": "Google",
            "title": "Intern",
            "employment_type": "internship",
            "work_mode": "remote",
            "url": "https://google.com/job1",
            "source": "google",
        },
        {
            "company": "Meta",
            "title": "Intern",
            "employment_type": "internship",
            "work_mode": "hybrid",
            "url": "https://meta.com/job1",
            "source": "meta",
        },
    ]

    internships = service.map_many(jobs)

    assert len(internships) == 2
    assert all(isinstance(job, Internship) for job in internships)
    assert internships[0].company == "Google"
    assert internships[1].company == "Meta"


def test_map_many_empty() -> None:
    """Verify empty input."""

    service = MapperService()

    assert service.map_many([]) == []
