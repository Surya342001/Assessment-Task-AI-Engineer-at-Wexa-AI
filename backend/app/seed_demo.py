from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.dashboard import Dashboard, WidgetType
from app.models.organization import UserRole
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SignUpRequest
from app.schemas.dashboard import DashboardCreate, QueryConfig, WidgetCreate, WidgetPosition
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService

DEMO_EMAIL = os.getenv("DEMO_USER_EMAIL", "surya@demo.com")
DEMO_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "Demo1234!")
DEMO_NAME = os.getenv("DEMO_USER_NAME", "Surya Demo")
DEMO_ORG = os.getenv("DEMO_ORGANIZATION_NAME", "Demo Analytics Workspace")


async def seed_demo() -> None:
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        org_repo = OrganizationRepository(db)
        user = await user_repo.get_by_email(DEMO_EMAIL)

        if user is None:
            await AuthService(db).sign_up(
                SignUpRequest(
                    email=DEMO_EMAIL,
                    password=DEMO_PASSWORD,
                    full_name=DEMO_NAME,
                    organization_name=DEMO_ORG,
                )
            )
            user = await user_repo.get_by_email(DEMO_EMAIL)
        else:
            user.hashed_password = hash_password(DEMO_PASSWORD)
            user.full_name = DEMO_NAME
            user.is_active = True
            user.is_verified = True
            await db.flush()

        if user is None:
            raise RuntimeError("Demo user could not be created")

        orgs = await org_repo.get_user_organizations(user.id)
        if orgs:
            org = orgs[0]
        else:
            org = await org_repo.create_organization(name=DEMO_ORG, owner_id=user.id)
            await org_repo.add_member(org_id=org.id, user_id=user.id, role=UserRole.OWNER)
            await db.commit()

        member = await org_repo.get_member(org.id, user.id)
        if member is None:
            await org_repo.add_member(org_id=org.id, user_id=user.id, role=UserRole.OWNER)
        elif member.role != UserRole.OWNER:
            member.role = UserRole.OWNER

        await _seed_events(db, org.id)
        await _seed_dashboard(db, org.id, user.id)
        await db.commit()
        print(f"Seeded demo login: {DEMO_EMAIL}")


async def _seed_events(db, org_id) -> None:
    event_repo = EventRepository(db)
    if await event_repo.count_events(org_id) > 0:
        return

    now = datetime.now(timezone.utc)
    names = ["page_view", "signup", "purchase", "api_request", "alert_triggered"]
    events = []
    for index in range(30):
        name = names[index % len(names)]
        events.append(
            {
                "name": name,
                "properties": {
                    "plan": ["free", "pro", "enterprise"][index % 3],
                    "region": ["IN", "US", "EU"][index % 3],
                    "value": (index + 1) * 7,
                },
                "timestamp": now - timedelta(hours=index * 2),
                "session_id": f"demo-session-{index % 6}",
                "user_id": f"demo-user-{index % 5}",
            }
        )
    await event_repo.create_events(org_id, events)


async def _seed_dashboard(db, org_id, user_id) -> None:
    existing = await db.execute(
        select(Dashboard).where(Dashboard.organization_id == org_id, Dashboard.name == "Demo Overview")
    )
    if existing.scalar_one_or_none() is not None:
        return

    await DashboardService(db).create_dashboard(
        org_id=org_id,
        user_id=user_id,
        data=DashboardCreate(
            name="Demo Overview",
            description="Seeded dashboard for hosted assignment review.",
            refresh_interval=60,
            widgets=[
                WidgetCreate(
                    widget_type=WidgetType.KPI_CARD,
                    title="Page Views",
                    query_config=QueryConfig(event_name="page_view", aggregation="count"),
                    position=WidgetPosition(x=0, y=0, w=3, h=2),
                ),
                WidgetCreate(
                    widget_type=WidgetType.LINE_CHART,
                    title="API Requests",
                    query_config=QueryConfig(event_name="api_request", aggregation="count", interval="1h"),
                    position=WidgetPosition(x=3, y=0, w=6, h=4),
                ),
                WidgetCreate(
                    widget_type=WidgetType.PIE_CHART,
                    title="Purchases By Plan",
                    query_config=QueryConfig(event_name="purchase", aggregation="count", group_by="plan"),
                    position=WidgetPosition(x=9, y=0, w=3, h=4),
                ),
            ],
        ),
    )


def main() -> None:
    asyncio.run(seed_demo())


if __name__ == "__main__":
    main()