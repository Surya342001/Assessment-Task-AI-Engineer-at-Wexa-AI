
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, to_http_exception
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.organization import (
    InviteMemberRequest,
    InvitationResponse,
    MemberResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateMemberRoleRequest,
)
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/orgs", tags=["Organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = OrganizationService(db)
        return await svc.create(data=data, owner_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = OrganizationService(db)
        return await svc.get_or_raise(org_id)
    except AppError as e:
        raise to_http_exception(e)


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    data: OrganizationUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = OrganizationService(db)
        return await svc.update(org_id=org_id, data=data, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def list_members(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        from app.repositories.organization_repository import OrganizationRepository
        repo = OrganizationRepository(db)
        return await repo.get_members(org_id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/{org_id}/members/invite", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: uuid.UUID,
    data: InviteMemberRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = OrganizationService(db)
        return await svc.invite_member(org_id=org_id, data=data, inviter_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/invitations/{token}/accept", status_code=status.HTTP_204_NO_CONTENT)
async def accept_invitation(
    token: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = OrganizationService(db)
        await svc.accept_invitation(token=token, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.patch("/{org_id}/members/{user_id}/role", response_model=MemberResponse)
async def update_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    data: UpdateMemberRoleRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = OrganizationService(db)
        return await svc.update_member_role(
            org_id=org_id,
            target_user_id=user_id,
            data=data,
            requester_id=current_user.id,
        )
    except AppError as e:
        raise to_http_exception(e)


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = OrganizationService(db)
        await svc.remove_member(
            org_id=org_id,
            target_user_id=user_id,
            requester_id=current_user.id,
        )
    except AppError as e:
        raise to_http_exception(e)
