"""Main FastAPI application configuration and router mapping."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.routers import (
    health_router,
    internships_router,
    notifications_router,
    pipeline_router,
    auth_router,
)
from app.core.config import settings
from app.core.logger import logger
from app.core.startup import Startup

__all__ = ["app"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application server startup and shutdown lifecycles."""
    logger.info("Initializing API application startup context.")
    try:
        startup_manager = Startup(settings=settings)
        startup_manager.run()
        logger.info("Application startup context verified successfully.")
    except Exception as exc:
        logger.critical("Application startup context verification failed: {}", exc)
        raise

    yield

    logger.info("Shutting down API application context.")


app = FastAPI(
    title="InternIntel API",
    version=settings.API_VERSION,
    description=(
        "Production-ready Internship Aggregation API supporting multiple ATS providers."
    ),
    lifespan=lifespan,
)

# Enable CORS for standard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralize exceptions responses
register_exception_handlers(app)

# Mount all resource endpoints under Version 1 prefix
v1_router = APIRouter(prefix=settings.API_PREFIX)
v1_router.include_router(health_router)
v1_router.include_router(internships_router)
v1_router.include_router(pipeline_router)
v1_router.include_router(notifications_router)
v1_router.include_router(auth_router)

app.include_router(v1_router)


@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["Root"],
    summary="Get API Root Information",
    description="Returns global details, system metadata, and versioning info.",
)
async def get_root() -> dict[str, str]:
    """Retrieve API meta details.

    Returns:
        Summary dictionary containing application name and version.
    """
    return {
        "application": "InternIntel",
        "version": settings.API_VERSION,
        "description": (
            "Production-ready Internship Aggregation API supporting multiple "
            "ATS providers."
        ),
        "api_version": settings.API_VERSION,
    }
