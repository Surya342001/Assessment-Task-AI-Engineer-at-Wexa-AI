
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.dashboard import Dashboard, Widget
from app.repositories.base import BaseRepository


class DashboardRepository(BaseRepository[Dashboard]):
    model = Dashboard

    async def get_org_dashboards(self, org_id: uuid.UUID) -> list[Dashboard]:
        result = await self.db.execute(
            select(Dashboard)
            .where(
                Dashboard.organization_id == org_id,
                Dashboard.is_deleted == False,
            )
            .options(selectinload(Dashboard.widgets))
            .order_by(Dashboard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_widgets(self, dashboard_id: uuid.UUID) -> Dashboard | None:
        result = await self.db.execute(
            select(Dashboard)
            .where(Dashboard.id == dashboard_id, Dashboard.is_deleted == False)
            .options(selectinload(Dashboard.widgets))
        )
        return result.scalar_one_or_none()

    async def get_by_public_slug(self, slug: str) -> Dashboard | None:
        result = await self.db.execute(
            select(Dashboard)
            .where(
                Dashboard.public_slug == slug,
                Dashboard.is_public == True,
                Dashboard.is_deleted == False,
            )
            .options(selectinload(Dashboard.widgets))
        )
        return result.scalar_one_or_none()

    async def create_dashboard(
        self,
        org_id: uuid.UUID,
        name: str,
        created_by_id: uuid.UUID,
        description: str | None = None,
        refresh_interval: int | None = None,
    ) -> Dashboard:
        return await self.create(
            organization_id=org_id,
            name=name,
            description=description,
            created_by_id=created_by_id,
            refresh_interval=refresh_interval,
        )

    async def make_public(self, dashboard: Dashboard) -> Dashboard:
        dashboard.is_public = True
        dashboard.public_slug = secrets.token_urlsafe(12)
        return await self.save(dashboard)

    async def make_private(self, dashboard: Dashboard) -> Dashboard:
        dashboard.is_public = False
        dashboard.public_slug = None
        return await self.save(dashboard)

    async def soft_delete(self, dashboard: Dashboard) -> None:
        dashboard.is_deleted = True
        await self.save(dashboard)


class WidgetRepository(BaseRepository[Widget]):
    model = Widget

    async def get_dashboard_widgets(self, dashboard_id: uuid.UUID) -> list[Widget]:
        result = await self.db.execute(
            select(Widget).where(Widget.dashboard_id == dashboard_id)
        )
        return list(result.scalars().all())

    async def create_widget(
        self,
        dashboard_id: uuid.UUID,
        widget_type,
        title: str,
        query_config: dict,
        position: dict,
        options: dict | None = None,
    ) -> Widget:
        return await self.create(
            dashboard_id=dashboard_id,
            widget_type=widget_type,
            title=title,
            query_config=query_config,
            position=position,
            options=options or {},
        )
