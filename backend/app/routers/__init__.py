from app.routers.auth import router as auth_router
from app.routers.organizations import router as org_router
from app.routers.events import router as events_router
from app.routers.dashboards import router as dashboards_router, public_router as public_dashboards_router
from app.routers.alerts import router as alerts_router
from app.routers.api_keys import router as api_keys_router

__all__ = [
    "auth_router",
    "org_router",
    "events_router",
    "dashboards_router",
    "public_dashboards_router",
    "alerts_router",
    "api_keys_router",
]
