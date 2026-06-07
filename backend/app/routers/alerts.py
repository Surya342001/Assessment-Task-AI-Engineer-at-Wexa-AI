
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, to_http_exception
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.alert import (
    AlertCreate,
    AlertHistoryResponse,
    AlertResponse,
    AlertUpdate,
    MuteAlertRequest,
)
from app.services.alert_service import AlertService

router = APIRouter(prefix="/orgs/{org_id}/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        return await svc.list_alerts(org_id=org_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    org_id: uuid.UUID,
    data: AlertCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        return await svc.create_alert(org_id=org_id, data=data, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    org_id: uuid.UUID,
    alert_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        return await svc.get_alert(org_id=org_id, alert_id=alert_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    org_id: uuid.UUID,
    alert_id: uuid.UUID,
    data: AlertUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        return await svc.update_alert(org_id=org_id, alert_id=alert_id, data=data, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    org_id: uuid.UUID,
    alert_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        await svc.delete_alert(org_id=org_id, alert_id=alert_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/{alert_id}/mute", response_model=AlertResponse)
async def mute_alert(
    org_id: uuid.UUID,
    alert_id: uuid.UUID,
    data: MuteAlertRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        return await svc.mute_alert(org_id=org_id, alert_id=alert_id, data=data, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/{alert_id}/unmute", response_model=AlertResponse)
async def unmute_alert(
    org_id: uuid.UUID,
    alert_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        return await svc.unmute_alert(org_id=org_id, alert_id=alert_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.get("/{alert_id}/history", response_model=list[AlertHistoryResponse])
async def get_alert_history(
    org_id: uuid.UUID,
    alert_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = AlertService(db)
        return await svc.get_alert_history(org_id=org_id, alert_id=alert_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)
