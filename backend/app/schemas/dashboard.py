
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.dashboard import WidgetType


class WidgetPosition(BaseModel):
    x: int = 0
    y: int = 0
    w: int = Field(default=6, ge=1, le=12)
    h: int = Field(default=4, ge=1, le=20)


class QueryConfig(BaseModel):
    event_name: str
    aggregation: str = "count"
    property_key: str | None = None
    group_by: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    time_range: str = "24h"  # 1h, 6h, 24h, 7d, 30d, 90d or custom
    interval: str = "1h"  # 5m, 15m, 1h, 1d


class WidgetCreate(BaseModel):
    widget_type: WidgetType
    title: str = Field(min_length=1, max_length=255)
    query_config: QueryConfig
    position: WidgetPosition = Field(default_factory=WidgetPosition)
    options: dict[str, Any] = Field(default_factory=dict)


class WidgetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    query_config: QueryConfig | None = None
    position: WidgetPosition | None = None
    options: dict[str, Any] | None = None


class WidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dashboard_id: uuid.UUID
    widget_type: WidgetType
    title: str
    query_config: dict[str, Any]
    position: dict[str, Any]
    options: dict[str, Any]
    created_at: datetime


class DashboardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    refresh_interval: int | None = Field(
        default=None, description="Refresh in seconds: 30, 60, 300"
    )
    widgets: list[WidgetCreate] = Field(default_factory=list)


class DashboardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    refresh_interval: int | None = None
    layout: list[dict] | None = None


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    layout: list[Any]
    is_public: bool
    public_slug: str | None
    refresh_interval: int | None
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    widgets: list[WidgetResponse]


class DashboardShareResponse(BaseModel):
    public_slug: str
    public_url: str
