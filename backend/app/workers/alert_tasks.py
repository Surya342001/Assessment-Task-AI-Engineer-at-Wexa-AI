
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.alert_tasks.evaluate_all_alerts", bind=True)
def evaluate_all_alerts(self) -> dict[str, Any]:
    """Evaluate all active alerts across all organizations."""
    try:
        result = asyncio.run(_evaluate_all_alerts_async())
        return result
    except Exception as exc:
        logger.error("alert_evaluation_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


async def _evaluate_all_alerts_async() -> dict[str, Any]:
    from app.database import AsyncSessionLocal
    from app.models.alert import Alert, AlertCondition, AlertStatus
    from app.repositories.alert_repository import AlertRepository
    from app.repositories.event_repository import EventRepository
    from app.services.notification_service import NotificationService

    triggered_count = 0
    resolved_count = 0

    async with AsyncSessionLocal() as db:
        alert_repo = AlertRepository(db)
        active_alerts = await alert_repo.get_active_alerts()

        for alert in active_alerts:
            # Skip muted alerts
            if alert.muted_until and alert.muted_until > datetime.now(timezone.utc):
                continue

            try:
                current_value = await _compute_metric(db, alert)
                is_triggered = _evaluate_condition(
                    current_value, alert.condition, alert.threshold
                )

                if is_triggered and alert.status != AlertStatus.TRIGGERED:
                    # Transition to triggered
                    alert.status = AlertStatus.TRIGGERED
                    msg = (
                        f"Alert '{alert.name}' triggered: "
                        f"value {current_value:.2f} {alert.condition.value} {alert.threshold:.2f}"
                    )
                    notification_svc = NotificationService()
                    sent = await notification_svc.send_alert_notification(
                        channels=alert.notification_channels,
                        alert_name=alert.name,
                        triggered_value=current_value,
                        threshold=alert.threshold,
                        message=msg,
                    )
                    await alert_repo.create_alert_history(
                        alert_id=alert.id,
                        triggered_value=current_value,
                        message=msg,
                        notifications_sent=sent,
                    )
                    # Broadcast via WebSocket
                    await _broadcast_alert(str(alert.organization_id), alert.id, msg)
                    triggered_count += 1

                elif not is_triggered and alert.status == AlertStatus.TRIGGERED:
                    alert.status = AlertStatus.RESOLVED
                    resolved_count += 1

                alert.last_evaluated_at = datetime.now(timezone.utc)

            except Exception as exc:
                logger.error("single_alert_eval_failed", alert_id=str(alert.id), error=str(exc))

        await db.commit()

    return {"triggered": triggered_count, "resolved": resolved_count, "total": len(active_alerts)}


async def _compute_metric(db, alert) -> float:
    from app.repositories.event_repository import EventRepository
    from datetime import timedelta

    repo = EventRepository(db)
    query = alert.metric_query
    start_time = datetime.now(timezone.utc) - timedelta(minutes=alert.window_minutes)

    count = await repo.count_events(
        org_id=alert.organization_id,
        start_time=start_time,
        event_name=query.get("event_name"),
    )
    return float(count)


def _evaluate_condition(value: float, condition, threshold: float) -> bool:
    from app.models.alert import AlertCondition
    mapping = {
        AlertCondition.GREATER_THAN: value > threshold,
        AlertCondition.LESS_THAN: value < threshold,
        AlertCondition.GREATER_THAN_OR_EQUAL: value >= threshold,
        AlertCondition.LESS_THAN_OR_EQUAL: value <= threshold,
        AlertCondition.EQUAL: value == threshold,
    }
    return mapping.get(condition, False)


async def _broadcast_alert(org_id: str, alert_id: uuid.UUID, message: str) -> None:
    import json
    import redis.asyncio as aioredis
    from app.config import settings

    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        channel = f"org:{org_id}:alerts"
        payload = json.dumps({
            "type": "alert_triggered",
            "alert_id": str(alert_id),
            "message": message,
        })
        await redis.publish(channel, payload)
    finally:
        await redis.aclose()
