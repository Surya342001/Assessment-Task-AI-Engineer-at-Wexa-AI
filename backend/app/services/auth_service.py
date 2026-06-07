from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.auth import SignUpRequest, SignInRequest, TokenResponse
from app.models.organization import UserRole


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def sign_up(self, data: SignUpRequest) -> tuple[TokenResponse, str]:
        """Register user + create org. Returns (token_response, refresh_token)."""
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already registered")

        hashed_pw = hash_password(data.password)
        user = await self.user_repo.create_user(
            email=data.email,
            hashed_password=hashed_pw,
            full_name=data.full_name,
        )

        org = await self.org_repo.create_organization(
            name=data.organization_name,
            owner_id=user.id,
        )

        await self.org_repo.add_member(
            org_id=org.id,
            user_id=user.id,
            role=UserRole.OWNER,
        )

        await self.db.commit()

        return await self._issue_tokens(user.id, org.id)

    async def sign_in(self, data: SignInRequest) -> tuple[TokenResponse, str]:
        user = await self.user_repo.get_active_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # Get user's first org
        orgs = await self.org_repo.get_user_organizations(user.id)
        org_id = orgs[0].id if orgs else None

        return await self._issue_tokens(user.id, org_id)

    async def refresh(self, raw_refresh_token: str) -> tuple[TokenResponse, str]:
        token_hash = hash_token(raw_refresh_token)
        token_obj = await self.refresh_token_repo.get_by_hash(token_hash)
        if token_obj is None:
            raise AuthenticationError("Invalid or expired refresh token")

        # Rotate: revoke old, issue new
        await self.refresh_token_repo.revoke_token(token_obj)

        user = await self.user_repo.get_by_id(token_obj.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        orgs = await self.org_repo.get_user_organizations(user.id)
        org_id = orgs[0].id if orgs else None

        result = await self._issue_tokens(user.id, org_id)
        await self.db.commit()
        return result

    async def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        token_obj = await self.refresh_token_repo.get_by_hash(token_hash)
        if token_obj:
            await self.refresh_token_repo.revoke_token(token_obj)
        await self.db.commit()

    async def _issue_tokens(
        self, user_id: uuid.UUID, org_id: uuid.UUID | None
    ) -> tuple[TokenResponse, str]:
        access_token = create_access_token(user_id, org_id)
        raw_refresh, refresh_hash, expires_at = create_refresh_token()

        await self.refresh_token_repo.create_token(
            user_id=user_id,
            token_hash=refresh_hash,
            expires_at=expires_at,
        )

        from app.config import settings
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return token_response, raw_refresh
