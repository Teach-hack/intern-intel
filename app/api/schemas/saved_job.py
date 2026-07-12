"""Pydantic schemas for Saved Internships."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.api.schemas.internship import InternshipResponse


class SavedJobResponse(BaseModel):
    """Schema representing a saved internship mapping."""

    id: int
    user_id: int
    internship_id: int
    notes: str | None
    created_at: datetime

    # Nested internship details to avoid N+1 queries from frontend
    internship: InternshipResponse

    model_config = ConfigDict(from_attributes=True)
