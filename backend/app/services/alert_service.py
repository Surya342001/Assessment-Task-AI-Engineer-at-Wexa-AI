
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.alert import AlertStatus
from app.models.organization import UserRole
from app.repositories.alert_repository import AlertRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.alert import AlertCreate, AlertUpdate, MuteAlertRequest


class AlertService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AlertRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def _check_access(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        member = await self.org_repo.get_member(org_id, user_id)
        if member is None:
            raise ForbiddenError("Not a member of this organization")
        if member.role == UserRole.VIEWER:
            raise ForbiddenError("Viewers cannot manage alerts")

    async def list_alerts(self, org_id: uuid.UUID, user_id: uuid.UUID):
        member = await self.org_repo.get_member(org_id, user_id)
        if member is None:
            raise ForbiddenError("Not a member of this organization")
        return await self.repo.get_org_alerts(org_id)

    async def create_alert(
        self, org_id: uuid.UUID, data: AlertCreate, user_id: uuid.UUID
    ):
        await self._check_access(org_id, user_id)
        alert = await self.repo.create(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            metric_query=data.metric_query,
            condition=data.condition,
            threshold=data.threshold,
            window_minutes=data.window_minutes,
            notification_channels=[c.model_dump() for c in data.notification_channels],
            created_by_id=user_id,
        )
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_alert(
        self, org_id: uuid.UUID, alert_id: uuid.UUID, user_id: uuid.UUID
    ):
        member = await self.org_repo.get_member(org_id, user_id)
        if member is None:
            raise ForbiddenError("Not a member of this organization")
        alert = await self.repo.get_by_id(alert_id)
        if alert is None or alert.organization_id != org_id or alert.is_deleted:
            raise NotFoundError("Alert", str(alert_id))
        return alert

    async def update_alert(
        self,
        org_id: uuid.UUID,
        alert_id: uuid.UUID,
        data: AlertUpdate,
        user_id: uuid.UUID,
    ):
        await self._check_access(org_id, user_id)
        alert = await self.get_alert(org_id, alert_id, user_id)

        if data.name is not None:
            alert.name = data.name
        if data.description is not None:
            alert.description = data.description
        if data.metric_query is not None:
            alert.metric_query = data.metric_query
        if data.condition is not None:
            alert.condition = data.condition
        if data.threshold is not None:
            alert.threshold = data.threshold
        if data.window_minutes is not None:
            alert.window_minutes = data.window_minutes
        if data.notification_channels is not None:
            alert.notification_channels = [c.model_dump() for c in data.notification_channels]

        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def delete_alert(
        self, org_id: uuid.UUID, alert_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await self._check_access(org_id, user_id)
        alert = await self.get_alert(org_id, alert_id, user_id)
        await self.repo.soft_delete(alert)
        await self.db.commit()

    async def mute_alert(
        self, org_id: uuid.UUID, alert_id: uuid.UUID, data: MuteAlertRequest, user_id: uuid.UUID
    ):
        await self._check_access(org_id, user_id)
        alert = await self.get_alert(org_id, alert_id, user_id)
        alert.status = AlertStatus.MUTED
        alert.muted_until = datetime.now(timezone.utc) + timedelta(minutes=data.duration_minutes)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def unmute_alert(
        self, org_id: uuid.UUID, alert_id: uuid.UUID, user_id: uuid.UUID
    ):
        await self._check_access(org_id, user_id)
        alert = await self.get_alert(org_id, alert_id, user_id)
        alert.status = AlertStatus.ACTIVE
        alert.muted_until = None
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_alert_history(
        self, org_id: uuid.UUID, alert_id: uuid.UUID, user_id: uuid.UUID
    ):
        alert = await self.get_alert(org_id, alert_id, user_id)
        return await self.repo.get_alert_history(alert_id)
