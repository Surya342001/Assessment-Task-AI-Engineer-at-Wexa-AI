from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, to_http_exception
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardResponse,
    DashboardShareResponse,
    DashboardUpdate,
    WidgetCreate,
    WidgetResponse,
    WidgetUpdate,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/orgs/{org_id}/dashboards", tags=["Dashboards"])
public_router = APIRouter(prefix="/public/dashboards", tags=["Public Dashboards"])


@router.get("", response_model=list[DashboardResponse], include_in_schema=False)
@router.get("/", response_model=list[DashboardResponse])
async def list_dashboards(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.list_dashboards(org_id=org_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    org_id: uuid.UUID,
    data: DashboardCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.create_dashboard(org_id=org_id, data=data, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.get_dashboard(org_id=org_id, dashboard_id=dashboard_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    data: DashboardUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.update_dashboard(
            org_id=org_id, dashboard_id=dashboard_id, data=data, user_id=current_user.id
        )
    except AppError as e:
        raise to_http_exception(e)


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        await svc.delete_dashboard(org_id=org_id, dashboard_id=dashboard_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/{dashboard_id}/share", response_model=DashboardShareResponse)
async def share_dashboard(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.share_dashboard(org_id=org_id, dashboard_id=dashboard_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.delete("/{dashboard_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_dashboard(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        await svc.unshare_dashboard(org_id=org_id, dashboard_id=dashboard_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


# Widget sub-routes
@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def add_widget(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    data: WidgetCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.add_widget(
            org_id=org_id, dashboard_id=dashboard_id, data=data, user_id=current_user.id
        )
    except AppError as e:
        raise to_http_exception(e)


@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    data: WidgetUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.update_widget(
            org_id=org_id, dashboard_id=dashboard_id, widget_id=widget_id, data=data, user_id=current_user.id
        )
    except AppError as e:
        raise to_http_exception(e)


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    org_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        await svc.delete_widget(
            org_id=org_id, dashboard_id=dashboard_id, widget_id=widget_id, user_id=current_user.id
        )
    except AppError as e:
        raise to_http_exception(e)


# Public dashboard (no auth required)
@public_router.get("/{slug}", response_model=DashboardResponse)
async def get_public_dashboard(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = DashboardService(db)
        return await svc.get_public_dashboard(slug=slug)
    except AppError as e:
        raise to_http_exception(e)
