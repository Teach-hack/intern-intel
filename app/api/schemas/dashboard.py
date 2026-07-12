"""Pydantic schemas for Dashboard."""

from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel
from app.api.schemas.internship import InternshipResponse


class DashboardOverviewStats(BaseModel):
    total_internships: int
    new_today: int
    saved_jobs: int
    companies: int


class DashboardCharts(BaseModel):
    source_distribution: Dict[str, int]


class DashboardRecent(BaseModel):
    internships: List[InternshipResponse]


class DashboardPipeline(BaseModel):
    last_run: datetime | None
    status: str


class DashboardSystem(BaseModel):
    version: str
    health: str


class DashboardResponse(BaseModel):
    """Schema representing the complete dashboard overview."""

    overview: DashboardOverviewStats
    charts: DashboardCharts
    recent: DashboardRecent
    pipeline: DashboardPipeline
    system: DashboardSystem
