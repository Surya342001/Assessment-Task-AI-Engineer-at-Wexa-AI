
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    """Only returned once on creation - includes the full key."""
    key: str


class ScheduledReportCreate(BaseModel):
    dashboard_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    schedule: str  # cron or "daily", "weekly", "monthly"
    recipients: list[str] = Field(min_length=1)


class ScheduledReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    dashboard_id: uuid.UUID
    name: str
    schedule: str
    recipients: list[str]
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
