
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.event import EventSource


class EventProperties(BaseModel):
    """Flexible event properties - any key/value pairs."""
    model_config = ConfigDict(extra="allow")


class SingleEventIngest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    properties: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None
    session_id: str | None = Field(default=None, max_length=255)
    user_id: str | None = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        return v.strip()


class BatchEventIngest(BaseModel):
    events: list[SingleEventIngest] = Field(min_length=1, max_length=1000)


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    properties: dict[str, Any]
    timestamp: datetime
    source: EventSource
    session_id: str | None
    user_id: str | None
    ingested_at: datetime


class EventIngestionResponse(BaseModel):
    accepted: int
    rejected: int
    event_ids: list[uuid.UUID]


class EventQueryFilters(BaseModel):
    event_names: list[str] | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    user_id: str | None = None
    session_id: str | None = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class EventAggregation(BaseModel):
    event_name: str
    aggregation: str = "count"  # count, sum, avg, min, max
    property_key: str | None = None
    group_by: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    interval: str = "1h"  # 5m, 15m, 1h, 1d, 1w
