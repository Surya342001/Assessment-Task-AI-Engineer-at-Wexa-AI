
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import generate_invite_token
from app.models.organization import UserRole
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.organization import (
    InviteMemberRequest,
    OrganizationCreate,
    OrganizationUpdate,
    UpdateMemberRoleRequest,
)
from app.services.notification_service import NotificationService


class OrganizationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = OrganizationRepository(db)
        self.user_repo = UserRepository(db)

    async def create(self, data: OrganizationCreate, owner_id: uuid.UUID):
        org = await self.repo.create_organization(name=data.name, owner_id=owner_id)
        await self.repo.add_member(
            org_id=org.id, user_id=owner_id, role=UserRole.OWNER
        )
        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def get_or_raise(self, org_id: uuid.UUID):
        org = await self.repo.get_by_id(org_id)
        if org is None:
            raise NotFoundError("Organization", str(org_id))
        return org

    async def update(self, org_id: uuid.UUID, data: OrganizationUpdate, user_id: uuid.UUID):
        org = await self.get_or_raise(org_id)
        member = await self.repo.get_member(org_id, user_id)
        if member is None or member.role not in (UserRole.OWNER, UserRole.ADMIN):
            raise ForbiddenError("Only Owner or Admin can update organization")
        if data.name:
            org.name = data.name
        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def invite_member(
        self,
        org_id: uuid.UUID,
        data: InviteMemberRequest,
        inviter_id: uuid.UUID,
    ):
        org = await self.get_or_raise(org_id)
        member = await self.repo.get_member(org_id, inviter_id)
        if member is None or member.role not in (UserRole.OWNER, UserRole.ADMIN):
            raise ForbiddenError("Only Owner or Admin can invite members")

        # Check if already a member
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            existing_member = await self.repo.get_member(org_id, existing_user.id)
            if existing_member:
                raise ConflictError("User is already a member of this organization")

        token = generate_invite_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        invitation = await self.repo.create_invitation(
            org_id=org_id,
            email=data.email,
            role=data.role,
            token=token,
            invited_by_id=inviter_id,
            expires_at=expires_at,
        )
        await self.db.commit()

        # Send invitation email asynchronously
        invite_link = f"{settings.FRONTEND_URL}/invite/{token}"
        notification_svc = NotificationService()
        await notification_svc.send_invitation_email(
            to_email=data.email,
            org_name=org.name,
            invite_link=invite_link,
        )

        await self.db.refresh(invitation)
        return invitation

    async def accept_invitation(self, token: str, user_id: uuid.UUID):
        invitation = await self.repo.get_invitation_by_token(token)
        if invitation is None:
            raise NotFoundError("Invitation")
        if invitation.accepted_at is not None:
            raise ConflictError("Invitation already accepted")
        if invitation.expires_at < datetime.now(timezone.utc):
            raise ConflictError("Invitation has expired")

        existing = await self.repo.get_member(invitation.organization_id, user_id)
        if existing:
            raise ConflictError("Already a member of this organization")

        await self.repo.add_member(
            org_id=invitation.organization_id,
            user_id=user_id,
            role=invitation.role,
            invited_by_id=invitation.invited_by_id,
        )
        invitation.accepted_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def update_member_role(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        data: UpdateMemberRoleRequest,
        requester_id: uuid.UUID,
    ):
        requester_member = await self.repo.get_member(org_id, requester_id)
        if requester_member is None or requester_member.role not in (UserRole.OWNER, UserRole.ADMIN):
            raise ForbiddenError("Only Owner or Admin can change roles")

        target_member = await self.repo.get_member(org_id, target_user_id)
        if target_member is None:
            raise NotFoundError("Member")
        if target_member.role == UserRole.OWNER:
            raise ForbiddenError("Cannot change the role of the organization owner")

        updated = await self.repo.update_member_role(target_member, data.role)
        await self.db.commit()
        return updated

    async def remove_member(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> None:
        requester_member = await self.repo.get_member(org_id, requester_id)
        if requester_member is None or requester_member.role not in (UserRole.OWNER, UserRole.ADMIN):
            raise ForbiddenError("Only Owner or Admin can remove members")

        target_member = await self.repo.get_member(org_id, target_user_id)
        if target_member is None:
            raise NotFoundError("Member")
        if target_member.role == UserRole.OWNER:
            raise ForbiddenError("Cannot remove organization owner")

        await self.repo.remove_member(target_member)
        await self.db.commit()
