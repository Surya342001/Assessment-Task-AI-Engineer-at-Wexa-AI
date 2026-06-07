from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.event import Event, EventSource
from app.repositories.base import BaseRepository
from app.schemas.event import EventQueryFilters


class EventRepository(BaseRepository[Event]):
    model = Event

    async def create_events(
        self,
        org_id: uuid.UUID,
        events_data: list[dict[str, Any]],
    ) -> list[Event]:
        """Bulk insert events efficiently."""
        await self._ensure_event_partitions(events_data)
        instances = [
            Event(
                organization_id=org_id,
                **data,
            )
            for data in events_data
        ]
        self.db.add_all(instances)
        await self.db.flush()
        for inst in instances:
            await self.db.refresh(inst)
        return instances

    async def _ensure_event_partitions(self, events_data: list[dict[str, Any]]) -> None:
        partition_days = set()
        for event_data in events_data:
            timestamp = event_data.get("timestamp")
            if not isinstance(timestamp, datetime):
                timestamp = datetime.now(timezone.utc)
            partition_days.add(timestamp.date())

        for partition_day in partition_days:
            next_day = partition_day + timedelta(days=1)
            partition_name = f"events_{partition_day:%Y%m%d}"
            await self.db.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF events
                    FOR VALUES FROM ('{partition_day.isoformat()}') TO ('{next_day.isoformat()}')
                    """
                )
            )

    async def get_events(
        self,
        org_id: uuid.UUID,
        filters: EventQueryFilters,
    ) -> list[Event]:
        query = select(Event).where(Event.organization_id == org_id)

        if filters.event_names:
            query = query.where(Event.name.in_(filters.event_names))
        if filters.start_time:
            query = query.where(Event.timestamp >= filters.start_time)
        if filters.end_time:
            query = query.where(Event.timestamp <= filters.end_time)
        if filters.user_id:
            query = query.where(Event.user_id == filters.user_id)
        if filters.session_id:
            query = query.where(Event.session_id == filters.session_id)

        query = query.order_by(Event.timestamp.desc())
        query = query.offset(filters.offset).limit(filters.limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_events(
        self,
        org_id: uuid.UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        event_name: str | None = None,
    ) -> int:
        query = select(func.count(Event.id)).where(Event.organization_id == org_id)

        if start_time:
            query = query.where(Event.timestamp >= start_time)
        if end_time:
            query = query.where(Event.timestamp <= end_time)
        if event_name:
            query = query.where(Event.name == event_name)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def aggregate_events(
        self,
        org_id: uuid.UUID,
        event_name: str,
        aggregation: str,
        property_key: str | None,
        group_by: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        interval: str,
    ) -> list[dict[str, Any]]:
        """Time-series aggregation query for chart widgets."""
        # Build time bucket
        interval_map = {
            "5m": "5 minutes",
            "15m": "15 minutes",
            "1h": "1 hour",
            "1d": "1 day",
            "1w": "1 week",
        }
        pg_interval = interval_map.get(interval, "1 hour")

        base_conds = [
            Event.organization_id == org_id,
            Event.name == event_name,
        ]
        if start_time:
            base_conds.append(Event.timestamp >= start_time)
        if end_time:
            base_conds.append(Event.timestamp <= end_time)

        where_clause = " AND ".join(
            [
                "organization_id = :org_id",
                "name = :event_name",
                *(["timestamp >= :start_time"] if start_time else []),
                *(["timestamp <= :end_time"] if end_time else []),
            ]
        )

        if aggregation == "count":
            agg_expr = "COUNT(*)"
        elif aggregation in ("sum", "avg", "min", "max") and property_key:
            agg_expr = f"{aggregation.upper()}((properties->>:property_key)::float)"
        else:
            agg_expr = "COUNT(*)"

        sql = f"""
            SELECT
                date_trunc(:bucket, timestamp) AS bucket,
                {agg_expr} AS value
                {f", properties->>:group_by_key AS group_key" if group_by else ""}
            FROM events
            WHERE {where_clause}
            GROUP BY bucket{", group_key" if group_by else ""}
            ORDER BY bucket ASC
        """

        params: dict[str, Any] = {
            "bucket": pg_interval,
            "org_id": org_id,
            "event_name": event_name,
        }
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if property_key:
            params["property_key"] = property_key
        if group_by:
            params["group_by_key"] = group_by

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()
        return [{"bucket": row[0], "value": row[1], **({"group_key": row[2]} if group_by else {})} for row in rows]
