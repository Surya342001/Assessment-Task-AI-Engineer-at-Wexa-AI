
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import generate_api_key
from app.models.organization import UserRole
from app.repositories.api_key_repository import APIKeyRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.api_key import APIKeyCreate, APIKeyCreatedResponse


class APIKeyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = APIKeyRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def _check_admin(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        member = await self.org_repo.get_member(org_id, user_id)
        if member is None or member.role not in (UserRole.OWNER, UserRole.ADMIN):
            raise ForbiddenError("Only Owner or Admin can manage API keys")

    async def list_keys(self, org_id: uuid.UUID, user_id: uuid.UUID):
        await self._check_admin(org_id, user_id)
        return await self.repo.get_org_keys(org_id)

    async def create_key(
        self, org_id: uuid.UUID, data: APIKeyCreate, user_id: uuid.UUID
    ) -> APIKeyCreatedResponse:
        await self._check_admin(org_id, user_id)
        raw_key, key_prefix, key_hash = generate_api_key()
        api_key = await self.repo.create_key(
            org_id=org_id,
            name=data.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            created_by_id=user_id,
        )
        await self.db.commit()
        await self.db.refresh(api_key)
        return APIKeyCreatedResponse(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            is_active=api_key.is_active,
            last_used_at=api_key.last_used_at,
            created_at=api_key.created_at,
            key=raw_key,
        )

    async def revoke_key(
        self, org_id: uuid.UUID, key_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await self._check_admin(org_id, user_id)
        api_key = await self.repo.get_by_id(key_id)
        if api_key is None or api_key.organization_id != org_id:
            raise NotFoundError("API Key", str(key_id))
        await self.repo.revoke_key(api_key)
        await self.db.commit()
