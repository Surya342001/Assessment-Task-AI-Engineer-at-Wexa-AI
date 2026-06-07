
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.routers import (
    auth_router,
    org_router,
    events_router,
    dashboards_router,
    public_dashboards_router,
    alerts_router,
    api_keys_router,
)
from app.routers.websocket import router as ws_router

# Configure structured logging
configure_logging()
logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Real-Time Analytics & Reporting Platform API",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request correlation ID middleware
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        from app.core.logging import bind_request_context
        bind_request_context(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Global exception handler for AppError
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message, "type": type(exc).__name__},
        )

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": settings.APP_NAME}

    @app.get("/api/health", tags=["Health"])
    async def api_health_check():
        return {"status": "healthy", "version": "1.0.0"}

    # Include API routers
    api_prefix = "/api"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(org_router, prefix=api_prefix)
    app.include_router(events_router, prefix=api_prefix)
    app.include_router(dashboards_router, prefix=api_prefix)
    app.include_router(public_dashboards_router, prefix=api_prefix)
    app.include_router(alerts_router, prefix=api_prefix)
    app.include_router(api_keys_router, prefix=api_prefix)
    app.include_router(ws_router, prefix="/api")

    @app.on_event("startup")
    async def startup_event():
        logger.info("application_started", env=settings.ENVIRONMENT)

    @app.on_event("shutdown")
    async def shutdown_event():
        from app.database import engine
        await engine.dispose()
        logger.info("application_shutdown")

    return app


app = create_app()
