
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.alert import Alert, AlertHistory, AlertStatus
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    async def get_org_alerts(self, org_id: uuid.UUID) -> list[Alert]:
        result = await self.db.execute(
            select(Alert)
            .where(Alert.organization_id == org_id, Alert.is_deleted == False)
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_alerts(self) -> list[Alert]:
        """Fetch all non-deleted, non-muted active alerts across all orgs (for Celery Beat)."""
        result = await self.db.execute(
            select(Alert)
            .where(
                Alert.is_deleted == False,
                Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.TRIGGERED]),
            )
        )
        return list(result.scalars().all())

    async def get_alert_history(
        self, alert_id: uuid.UUID, limit: int = 50
    ) -> list[AlertHistory]:
        result = await self.db.execute(
            select(AlertHistory)
            .where(AlertHistory.alert_id == alert_id)
            .order_by(AlertHistory.triggered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_alert_history(
        self,
        alert_id: uuid.UUID,
        triggered_value: float,
        message: str,
        notifications_sent: list | None = None,
    ) -> AlertHistory:
        history = AlertHistory(
            alert_id=alert_id,
            triggered_value=triggered_value,
            message=message,
            notifications_sent=notifications_sent or [],
        )
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        return history

    async def soft_delete(self, alert: Alert) -> None:
        alert.is_deleted = True
        await self.save(alert)


class APIKeyRepository(BaseRepository):
    from app.models.api_key import APIKey
    model = APIKey

    async def validate_key(self, raw_key: str) -> "Organization | None":  # type: ignore[name-defined]
        from app.core.security import hash_token
        from app.models.api_key import APIKey
        from app.models.organization import Organization
        from datetime import datetime, timezone

        key_hash = hash_token(raw_key)
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.key_hash == key_hash, APIKey.is_active == True)
            .options(selectinload(APIKey.organization))
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            return None
        # Update last_used_at
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()
        return api_key.organization
