"""Pydantic schemas for standardized API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "HealthResponse",
    "StatsResponse",
    "PipelineRunResponse",
    "NotificationRequest",
    "ErrorResponse",
]


class HealthResponse(BaseModel):
    """Pydantic schema representing the application and service health metrics."""

    status: str = Field(description="Overall system health status, e.g., healthy.")
    database: str = Field(description="Database connection state status.")
    scheduler: str = Field(description="Scheduler thread execution state.")
    notifications: str = Field(
        description="Status of dispatch notifications configuration."
    )
    registered_scrapers: int = Field(
        description="Number of ATS scraper providers registered."
    )
    version: str = Field(description="Application version identifier.")
    uptime_seconds: int = Field(description="Number of seconds since server startup.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "database": "connected",
                "scheduler": "running",
                "notifications": "enabled",
                "registered_scrapers": 8,
                "version": "1.0.0",
                "uptime_seconds": 532,
            }
        }
    }


class StatsResponse(BaseModel):
    """Pydantic schema representing aggregated internship database statistics."""

    total: int = Field(description="Total number of internships stored.")
    new_today: int = Field(description="Number of internship listings added today.")
    companies: int = Field(description="Number of unique company names represented.")
    sources: dict[str, int] = Field(
        description="Breakdown of internship counts grouped by source scraper."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 1200,
                "new_today": 18,
                "companies": 145,
                "sources": {"greenhouse": 400, "lever": 250, "workday": 550},
            }
        }
    }


class PipelineRunResponse(BaseModel):
    """Pydantic schema representing the result of a scraper pipeline execution."""

    jobs_discovered: int = Field(
        description="Number of job listings found by scrapers."
    )
    jobs_inserted: int = Field(
        description="Number of newly discovered jobs saved to database."
    )
    execution_status: str = Field(
        description="Pipeline execution result status, e.g., success."
    )
    execution_time: float = Field(description="Total execution time in seconds.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "jobs_discovered": 45,
                "jobs_inserted": 12,
                "execution_status": "success",
                "execution_time": 4.12,
            }
        }
    }


class NotificationRequest(BaseModel):
    """Pydantic schema representing the request body to trigger notifications."""

    internship_ids: list[int] = Field(
        description="List of database internship IDs to send notifications for."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "internship_ids": [1, 2, 3],
            }
        }
    }


class ErrorResponse(BaseModel):
    """Pydantic schema representing a standardized error message response."""

    detail: str = Field(
        description="Detailed error message explaining the failure reason."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Requested internship resource not found.",
            }
        }
    }
