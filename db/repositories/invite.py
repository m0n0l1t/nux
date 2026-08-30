from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from db.models import Invite


class InviteRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        creator_id: int,
        expires_at: datetime = None
    ) -> Invite:
        code = str(uuid.uuid4())
        invite = Invite(code=code, creator_user_id=creator_id, expires_at=expires_at)
        db.add(invite)
        await db.commit()
        await db.refresh(invite)
        return invite

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Invite | None:
        result = await db.execute(select(Invite).where(Invite.code == code))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_creator(db: AsyncSession, creator_id: int) -> list[Invite]:
        result = await db.execute(select(Invite).where(Invite.creator_user_id == creator_id))
        return result.scalars().all()

    @staticmethod
    async def use_invite(db: AsyncSession, code: str, user_id: int) -> bool:
        invite = await InviteRepository.get_by_code(db, code)
        if not invite or invite.used_by_user_id or (invite.expires_at and invite.expires_at < datetime.utcnow()):
            return False
        invite.used_by_user_id = user_id
        invite.used_at = datetime.utcnow()
        await db.commit()
        return True