"""Router for triggering and monitoring the scraping pipeline execution."""

from __future__ import annotations

import time
import json

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_pipeline_service, get_db_session
from app.security.rbac import Permission, require_permissions
from app.api.schemas.response import PipelineRunResponse, PipelineStatusResponse
from app.services.pipeline_service import PipelineService
from app.models.audit_log import AuditLog
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(tags=["Pipeline"])


@router.get(
    "/pipeline/status",
    response_model=PipelineStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Pipeline Status",
    description="Returns the current status and metrics of the scraper pipeline.",
    dependencies=[Depends(require_permissions([Permission.PIPELINE_EXECUTE]))],
)
async def get_pipeline_status(
    session: Session = Depends(get_db_session),
) -> PipelineStatusResponse:
    """Retrieve detailed pipeline status."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.action == "PIPELINE_EXECUTE")
        .order_by(AuditLog.timestamp.desc())
        .limit(1)
    )
    last_run = session.execute(stmt).scalar_one_or_none()

    # Simple mocked up response for now since we don't have a background task queue yet.
    # In a full celery/arq setup we'd query the broker.
    is_running = False

    return PipelineStatusResponse(
        running=is_running,
        last_run=last_run.timestamp if last_run else None,
        last_success=last_run.timestamp
        if last_run and last_run.status == "success"
        else None,
        last_failure=last_run.timestamp
        if last_run and last_run.status == "failure"
        else None,
        duration=None,
        queue_length=0,
        currently_running_scrapers=[],
        next_scheduled_run=None,
        scrapers_executed=8,
        jobs_discovered=json.loads(last_run.details).get("jobs_discovered", 0)
        if last_run and last_run.details
        else 0,
        jobs_inserted=json.loads(last_run.details).get("jobs_inserted", 0)
        if last_run and last_run.details
        else 0,
        jobs_updated=0,
        errors=0,
    )


@router.post(
    "/pipeline/run",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Scraper Pipeline",
    description=(
        "Triggers the scraper pipeline orchestration sequence to fetch new "
        "listings, filter duplicates, and persist updates."
    ),
    dependencies=[Depends(require_permissions([Permission.PIPELINE_EXECUTE]))],
)
async def run_pipeline(
    pipeline_service: PipelineService = Depends(get_pipeline_service),
) -> PipelineRunResponse:
    """Execute default scrapers pipeline, recording run time and items count.

    Args:
        pipeline_service: Injected PipelineService instance.

    Returns:
        PipelineRunResponse status payload.
    """
    start_time = time.perf_counter()
    inserted = pipeline_service.run()
    duration = time.perf_counter() - start_time

    return PipelineRunResponse(
        jobs_discovered=pipeline_service.last_run_discovered,
        jobs_inserted=len(inserted),
        execution_status="success",
        execution_time=round(duration, 3),
    )
