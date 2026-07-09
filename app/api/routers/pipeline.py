"""Router for triggering and monitoring the scraping pipeline execution."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_admin_user, get_pipeline_service
from app.api.schemas.response import PipelineRunResponse
from app.services.pipeline_service import PipelineService

router = APIRouter(tags=["Pipeline"])


@router.post(
    "/pipeline/run",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Scraper Pipeline",
    description=(
        "Triggers the scraper pipeline orchestration sequence to fetch new "
        "listings, filter duplicates, and persist updates."
    ),
    dependencies=[Depends(get_admin_user)],
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
