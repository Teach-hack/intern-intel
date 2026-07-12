"""Service layer for dashboard data aggregation."""

from typing import Any, Dict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.saved_job import SavedJob
from app.models.audit_log import AuditLog
from app.services.database_service import DatabaseService
from app.core.settings import Settings


class DashboardService:
    """Business logic for dashboard metrics aggregation."""

    def __init__(
        self, session: Session, settings: Settings, db_service: DatabaseService
    ) -> None:
        self._session = session
        self._settings = settings
        self._db_service = db_service

    def get_overview(self) -> Dict[str, Any]:
        """Aggregate all dashboard metrics."""

        # 1. Base statistics from existing database service
        stats = self._db_service.get_statistics()

        # 2. Saved jobs count
        saved_jobs_count = self._session.scalar(select(func.count(SavedJob.id))) or 0

        # 3. Recent internships
        recent = self._db_service.query_internships(
            limit=5, sort_by="created_at", order="desc"
        )

        # 4. Pipeline status (from AuditLog)
        # Look for the last PIPELINE_EXECUTE event
        stmt = (
            select(AuditLog)
            .where(AuditLog.action == "PIPELINE_EXECUTE")
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        last_pipeline_log = self._session.execute(stmt).scalar_one_or_none()

        pipeline_status = {
            "last_run": last_pipeline_log.timestamp if last_pipeline_log else None,
            "status": "idle",  # Assuming idle unless a background thread is active
        }

        return {
            "overview": {
                "total_internships": stats["total"],
                "new_today": stats["new_today"],
                "saved_jobs": saved_jobs_count,
                "companies": stats["companies"],
            },
            "charts": {"source_distribution": stats["sources"]},
            "recent": {"internships": recent},
            "pipeline": pipeline_status,
            "system": {"version": self._settings.API_VERSION, "health": "healthy"},
        }
