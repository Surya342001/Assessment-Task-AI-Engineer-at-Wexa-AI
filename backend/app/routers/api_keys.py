
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, to_http_exception
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyCreatedResponse, APIKeyResponse
from app.services.api_key_service import APIKeyService

router = APIRouter(prefix="/orgs/{org_id}/api-keys", tags=["API Keys"])


@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = APIKeyService(db)
        return await svc.list_keys(org_id=org_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.post("/", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    org_id: uuid.UUID,
    data: APIKeyCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create an API key. The full key is only shown once."""
    try:
        svc = APIKeyService(db)
        return await svc.create_key(org_id=org_id, data=data, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    org_id: uuid.UUID,
    key_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = APIKeyService(db)
        await svc.revoke_key(org_id=org_id, key_id=key_id, user_id=current_user.id)
    except AppError as e:
        raise to_http_exception(e)
