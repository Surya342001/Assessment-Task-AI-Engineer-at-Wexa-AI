
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, to_http_exception
from app.core.rate_limit import limiter
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.event import EventSource
from app.models.user import User
from app.schemas.event import (
    BatchEventIngest,
    EventAggregation,
    EventIngestionResponse,
    EventQueryFilters,
    EventResponse,
    SingleEventIngest,
)
from app.services.event_service import EventService

router = APIRouter(prefix="/orgs/{org_id}/events", tags=["Events"])


@router.post("/ingest", response_model=EventIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("1000/minute")
async def ingest_single_event(
    request: Request,
    org_id: uuid.UUID,
    data: SingleEventIngest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Ingest a single event for an organization."""
    try:
        svc = EventService(db)
        ip = request.client.host if request.client else None
        return await svc.ingest_single(org_id=org_id, data=data, ip_address=ip)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/ingest/batch", response_model=EventIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("100/minute")
async def ingest_batch_events(
    request: Request,
    org_id: uuid.UUID,
    data: BatchEventIngest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Ingest a batch of events (up to 1000 per request)."""
    try:
        svc = EventService(db)
        ip = request.client.host if request.client else None
        return await svc.ingest_batch(org_id=org_id, data=data, ip_address=ip)
    except AppError as e:
        raise to_http_exception(e)


@router.get("/", response_model=list[EventResponse])
async def list_events(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
    offset: int = 0,
):
    """List recent events for an organization."""
    try:
        svc = EventService(db)
        filters = EventQueryFilters(limit=limit, offset=offset)
        return await svc.query_events(org_id=org_id, filters=filters)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/aggregate")
async def aggregate_events(
    org_id: uuid.UUID,
    params: EventAggregation,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Aggregate events for chart rendering."""
    try:
        svc = EventService(db)
        return await svc.aggregate(org_id=org_id, params=params)
    except AppError as e:
        raise to_http_exception(e)
