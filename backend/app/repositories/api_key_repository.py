
import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.api_key import APIKey
from app.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    model = APIKey

    async def get_org_keys(self, org_id: uuid.UUID) -> list[APIKey]:
        result = await self.db.execute(
            select(APIKey).where(APIKey.organization_id == org_id, APIKey.is_active == True)
        )
        return list(result.scalars().all())

    async def validate_key(self, raw_key: str) -> "Organization | None":  # type: ignore[name-defined]
        from sqlalchemy.orm import selectinload
        from app.models.organization import Organization

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.key_hash == key_hash, APIKey.is_active == True)
            .options(selectinload(APIKey.organization))
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            return None
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()
        return api_key.organization

    async def create_key(
        self,
        org_id: uuid.UUID,
        name: str,
        key_prefix: str,
        key_hash: str,
        created_by_id: uuid.UUID | None = None,
    ) -> APIKey:
        return await self.create(
            organization_id=org_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            created_by_id=created_by_id,
        )

    async def revoke_key(self, api_key: APIKey) -> APIKey:
        api_key.is_active = False
        return await self.save(api_key)
