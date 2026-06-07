
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.event import EventSource
from app.repositories.event_repository import EventRepository
from app.schemas.event import (
    BatchEventIngest,
    EventAggregation,
    EventIngestionResponse,
    EventQueryFilters,
    SingleEventIngest,
)
from app.workers.event_tasks import process_events_task


class EventService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = EventRepository(db)

    async def ingest_single(
        self,
        org_id: uuid.UUID,
        data: SingleEventIngest,
        source: EventSource = EventSource.API,
        ip_address: str | None = None,
    ) -> EventIngestionResponse:
        ts = data.timestamp or datetime.now(timezone.utc)
        events = await self.repo.create_events(
            org_id=org_id,
            events_data=[
                {
                    "name": data.name,
                    "properties": data.properties,
                    "timestamp": ts,
                    "source": source,
                    "session_id": data.session_id,
                    "user_id": data.user_id,
                    "ip_address": ip_address,
                }
            ],
        )
        await self.db.commit()

        # Push to Celery for downstream processing
        process_events_task.delay(
            org_id=str(org_id),
            event_ids=[str(e.id) for e in events],
        )

        return EventIngestionResponse(
            accepted=len(events),
            rejected=0,
            event_ids=[e.id for e in events],
        )

    async def ingest_batch(
        self,
        org_id: uuid.UUID,
        data: BatchEventIngest,
        source: EventSource = EventSource.API,
        ip_address: str | None = None,
    ) -> EventIngestionResponse:
        events_data = []
        for event in data.events:
            ts = event.timestamp or datetime.now(timezone.utc)
            events_data.append(
                {
                    "name": event.name,
                    "properties": event.properties,
                    "timestamp": ts,
                    "source": source,
                    "session_id": event.session_id,
                    "user_id": event.user_id,
                    "ip_address": ip_address,
                }
            )

        events = await self.repo.create_events(org_id=org_id, events_data=events_data)
        await self.db.commit()

        process_events_task.delay(
            org_id=str(org_id),
            event_ids=[str(e.id) for e in events],
        )

        return EventIngestionResponse(
            accepted=len(events),
            rejected=0,
            event_ids=[e.id for e in events],
        )

    async def query_events(
        self, org_id: uuid.UUID, filters: EventQueryFilters
    ) -> list:
        return await self.repo.get_events(org_id=org_id, filters=filters)

    async def aggregate(
        self, org_id: uuid.UUID, params: EventAggregation
    ) -> list[dict[str, Any]]:
        return await self.repo.aggregate_events(
            org_id=org_id,
            event_name=params.event_name,
            aggregation=params.aggregation,
            property_key=params.property_key,
            group_by=params.group_by,
            start_time=params.start_time,
            end_time=params.end_time,
            interval=params.interval,
        )
