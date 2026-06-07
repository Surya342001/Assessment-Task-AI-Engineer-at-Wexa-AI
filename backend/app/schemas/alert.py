
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertCondition, AlertStatus


class NotificationChannel(BaseModel):
    type: str  # email, webhook, in_app
    config: dict[str, Any] = Field(default_factory=dict)


class AlertCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    metric_query: dict[str, Any]
    condition: AlertCondition
    threshold: float
    window_minutes: int = Field(default=5, ge=1, le=1440)
    notification_channels: list[NotificationChannel] = Field(default_factory=list)


class AlertUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    metric_query: dict[str, Any] | None = None
    condition: AlertCondition | None = None
    threshold: float | None = None
    window_minutes: int | None = Field(default=None, ge=1, le=1440)
    notification_channels: list[NotificationChannel] | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    metric_query: dict[str, Any]
    condition: AlertCondition
    threshold: float
    window_minutes: int
    status: AlertStatus
    notification_channels: list[Any]
    muted_until: datetime | None
    last_evaluated_at: datetime | None
    created_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class AlertHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    alert_id: uuid.UUID
    triggered_at: datetime
    resolved_at: datetime | None
    triggered_value: float
    message: str


class MuteAlertRequest(BaseModel):
    duration_minutes: int = Field(ge=1, le=10080)  # max 1 week
