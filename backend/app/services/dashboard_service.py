
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.dashboard_repository import DashboardRepository, WidgetRepository
from app.repositories.organization_repository import OrganizationRepository
from app.models.organization import UserRole
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardShareResponse,
    DashboardUpdate,
    WidgetCreate,
    WidgetUpdate,
)


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.dashboard_repo = DashboardRepository(db)
        self.widget_repo = WidgetRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def _check_access(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        min_role: UserRole = UserRole.VIEWER,
    ) -> None:
        member = await self.org_repo.get_member(org_id, user_id)
        if member is None:
            raise ForbiddenError("Not a member of this organization")
        role_order = {
            UserRole.VIEWER: 0,
            UserRole.ANALYST: 1,
            UserRole.ADMIN: 2,
            UserRole.OWNER: 3,
        }
        if role_order[member.role] < role_order[min_role]:
            raise ForbiddenError("Insufficient permissions")

    async def list_dashboards(self, org_id: uuid.UUID, user_id: uuid.UUID):
        await self._check_access(org_id, user_id)
        return await self.dashboard_repo.get_org_dashboards(org_id)

    async def create_dashboard(
        self, org_id: uuid.UUID, data: DashboardCreate, user_id: uuid.UUID
    ):
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        dashboard = await self.dashboard_repo.create_dashboard(
            org_id=org_id,
            name=data.name,
            created_by_id=user_id,
            description=data.description,
            refresh_interval=data.refresh_interval,
        )
        # Create widgets if provided
        for widget_data in data.widgets:
            await self.widget_repo.create_widget(
                dashboard_id=dashboard.id,
                widget_type=widget_data.widget_type,
                title=widget_data.title,
                query_config=widget_data.query_config.model_dump(),
                position=widget_data.position.model_dump(),
                options=widget_data.options,
            )
        await self.db.commit()
        return await self.dashboard_repo.get_with_widgets(dashboard.id)

    async def get_dashboard(
        self, org_id: uuid.UUID, dashboard_id: uuid.UUID, user_id: uuid.UUID
    ):
        await self._check_access(org_id, user_id)
        dashboard = await self.dashboard_repo.get_with_widgets(dashboard_id)
        if dashboard is None or dashboard.organization_id != org_id:
            raise NotFoundError("Dashboard", str(dashboard_id))
        return dashboard

    async def get_public_dashboard(self, slug: str):
        dashboard = await self.dashboard_repo.get_by_public_slug(slug)
        if dashboard is None:
            raise NotFoundError("Dashboard")
        return dashboard

    async def update_dashboard(
        self,
        org_id: uuid.UUID,
        dashboard_id: uuid.UUID,
        data: DashboardUpdate,
        user_id: uuid.UUID,
    ):
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        dashboard = await self.dashboard_repo.get_with_widgets(dashboard_id)
        if dashboard is None or dashboard.organization_id != org_id:
            raise NotFoundError("Dashboard", str(dashboard_id))

        if data.name is not None:
            dashboard.name = data.name
        if data.description is not None:
            dashboard.description = data.description
        if data.refresh_interval is not None:
            dashboard.refresh_interval = data.refresh_interval
        if data.layout is not None:
            dashboard.layout = data.layout

        await self.db.commit()
        return await self.dashboard_repo.get_with_widgets(dashboard_id)

    async def delete_dashboard(
        self, org_id: uuid.UUID, dashboard_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        dashboard = await self.dashboard_repo.get_by_id(dashboard_id)
        if dashboard is None or dashboard.organization_id != org_id:
            raise NotFoundError("Dashboard", str(dashboard_id))
        await self.dashboard_repo.soft_delete(dashboard)
        await self.db.commit()

    async def share_dashboard(
        self, org_id: uuid.UUID, dashboard_id: uuid.UUID, user_id: uuid.UUID
    ) -> DashboardShareResponse:
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        dashboard = await self.dashboard_repo.get_by_id(dashboard_id)
        if dashboard is None or dashboard.organization_id != org_id:
            raise NotFoundError("Dashboard", str(dashboard_id))
        dashboard = await self.dashboard_repo.make_public(dashboard)
        await self.db.commit()
        return DashboardShareResponse(
            public_slug=dashboard.public_slug,
            public_url=f"{settings.FRONTEND_URL}/public/dashboards/{dashboard.public_slug}",
        )

    async def unshare_dashboard(
        self, org_id: uuid.UUID, dashboard_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        dashboard = await self.dashboard_repo.get_by_id(dashboard_id)
        if dashboard is None or dashboard.organization_id != org_id:
            raise NotFoundError("Dashboard", str(dashboard_id))
        await self.dashboard_repo.make_private(dashboard)
        await self.db.commit()

    async def add_widget(
        self,
        org_id: uuid.UUID,
        dashboard_id: uuid.UUID,
        data: WidgetCreate,
        user_id: uuid.UUID,
    ):
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        dashboard = await self.dashboard_repo.get_by_id(dashboard_id)
        if dashboard is None or dashboard.organization_id != org_id:
            raise NotFoundError("Dashboard", str(dashboard_id))
        widget = await self.widget_repo.create_widget(
            dashboard_id=dashboard_id,
            widget_type=data.widget_type,
            title=data.title,
            query_config=data.query_config.model_dump(),
            position=data.position.model_dump(),
            options=data.options,
        )
        await self.db.commit()
        await self.db.refresh(widget)
        return widget

    async def update_widget(
        self,
        org_id: uuid.UUID,
        dashboard_id: uuid.UUID,
        widget_id: uuid.UUID,
        data: WidgetUpdate,
        user_id: uuid.UUID,
    ):
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        widget = await self.widget_repo.get_by_id(widget_id)
        if widget is None or widget.dashboard_id != dashboard_id:
            raise NotFoundError("Widget", str(widget_id))

        if data.title is not None:
            widget.title = data.title
        if data.query_config is not None:
            widget.query_config = data.query_config.model_dump()
        if data.position is not None:
            widget.position = data.position.model_dump()
        if data.options is not None:
            widget.options = data.options

        await self.db.commit()
        await self.db.refresh(widget)
        return widget

    async def delete_widget(
        self,
        org_id: uuid.UUID,
        dashboard_id: uuid.UUID,
        widget_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._check_access(org_id, user_id, UserRole.ANALYST)
        widget = await self.widget_repo.get_by_id(widget_id)
        if widget is None or widget.dashboard_id != dashboard_id:
            raise NotFoundError("Widget", str(widget_id))
        await self.widget_repo.delete(widget)
        await self.db.commit()
