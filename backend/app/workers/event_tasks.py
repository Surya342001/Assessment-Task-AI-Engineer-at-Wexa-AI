
import asyncio
import uuid
from typing import Any

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.workers.event_tasks.process_events_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def process_events_task(
    self,
    org_id: str,
    event_ids: list[str],
) -> dict[str, Any]:
    """
    Post-ingestion processing:
    - Broadcast new events to WebSocket subscribers
    - Update real-time counters in Redis
    - Trigger alert evaluations if needed
    """
    try:
        asyncio.run(_process_events_async(org_id=org_id, event_ids=event_ids))
        return {"processed": len(event_ids), "org_id": org_id}
    except Exception as exc:
        logger.error("event_processing_failed", org_id=org_id, error=str(exc))
        raise self.retry(exc=exc)


async def _process_events_async(org_id: str, event_ids: list[str]) -> None:
    import redis.asyncio as aioredis
    import json
    from app.config import settings

    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        # Publish to WebSocket channel for real-time updates
        channel = f"org:{org_id}:events"
        message = json.dumps({
            "type": "new_events",
            "org_id": org_id,
            "event_ids": event_ids,
            "count": len(event_ids),
        })
        await redis.publish(channel, message)

        # Increment event counter for the org
        await redis.incr(f"org:{org_id}:event_count")
        logger.info("events_processed", org_id=org_id, count=len(event_ids))
    finally:
        await redis.aclose()
