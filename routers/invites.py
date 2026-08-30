from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.auth import get_current_user
from db.models import User
from core.schemas import InviteCreateRequest, InviteResponse
from db.repositories import InviteRepository

router = APIRouter(prefix="/invites", tags=["Invites"])

@router.post("", response_model=InviteResponse)
async def create_invite(request: InviteCreateRequest = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    expires_at = request.expires_at if request else None
    invite = await InviteRepository.create(db, current_user.id, expires_at)
    return invite

@router.get("", response_model=list[InviteResponse])
async def list_invites(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    invites = await InviteRepository.get_by_creator(db, current_user.id)
    return invites
