
import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.organization import Invitation, Organization, OrganizationMember, UserRole
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_organization(
        self,
        name: str,
        owner_id: uuid.UUID,
    ) -> Organization:
        slug = await self._generate_unique_slug(name)
        return await self.create(name=name, slug=slug, owner_id=owner_id)

    async def _generate_unique_slug(self, name: str) -> str:
        base_slug = re.sub(r"[^a-z0-9-]", "-", name.lower().strip())
        base_slug = re.sub(r"-+", "-", base_slug).strip("-")
        slug = base_slug
        counter = 1
        while await self.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    async def get_member(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMember | None:
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_members(self, org_id: uuid.UUID) -> list[OrganizationMember]:
        result = await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
            .options(selectinload(OrganizationMember.user))
        )
        return list(result.scalars().all())

    async def add_member(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        role: UserRole,
        invited_by_id: uuid.UUID | None = None,
    ) -> OrganizationMember:
        member = OrganizationMember(
            organization_id=org_id,
            user_id=user_id,
            role=role,
            invited_by_id=invited_by_id,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def update_member_role(
        self, member: OrganizationMember, role: UserRole
    ) -> OrganizationMember:
        member.role = role
        return await self.save(member)

    async def remove_member(self, member: OrganizationMember) -> None:
        await self.delete(member)

    async def get_user_organizations(self, user_id: uuid.UUID) -> list[Organization]:
        result = await self.db.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_invitation_by_token(self, token: str) -> Invitation | None:
        result = await self.db.execute(
            select(Invitation).where(Invitation.token == token)
        )
        return result.scalar_one_or_none()

    async def create_invitation(
        self,
        org_id: uuid.UUID,
        email: str,
        role: UserRole,
        token: str,
        invited_by_id: uuid.UUID,
        expires_at,
    ) -> Invitation:
        invitation = Invitation(
            organization_id=org_id,
            email=email,
            role=role,
            token=token,
            invited_by_id=invited_by_id,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        await self.db.flush()
        await self.db.refresh(invitation)
        return invitation
