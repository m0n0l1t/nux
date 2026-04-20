from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
from db.database import get_db
from db.models import User
from db import crud
from core.schemas import AdminInviteCreateRequest, InviteResponse, AdminTopUpRequest, BalanceResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_UUID = os.getenv("ADMIN_UUID")
if not ADMIN_UUID:
    raise RuntimeError("ADMIN_UUID environment variable is required")

@router.post("/invites", response_model=InviteResponse)
async def admin_create_invite(
    request: AdminInviteCreateRequest,
    x_admin_uuid: str = Header(alias="X-Admin-UUID"),
    db: AsyncSession = Depends(get_db)
):
    if x_admin_uuid != ADMIN_UUID:
        raise HTTPException(403, "Invalid admin UUID")
    # берём первого пользователя как админа
    result = await db.execute(select(User).limit(1))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(400, "No user exists")
    invite = await crud.create_invite(db, admin.id, request.expires_at)
    return invite

@router.post("/topup", response_model=BalanceResponse)
async def admin_topup_balance(
    request: AdminTopUpRequest,
    x_admin_uuid: str = Header(alias="X-Admin-UUID"),
    db: AsyncSession = Depends(get_db)
):
    """Админское начисление звёзд пользователю (для тестов)"""
    if x_admin_uuid != ADMIN_UUID:
        raise HTTPException(403, "Invalid admin UUID")
    
    # Ищем пользователя по username или user_id
    user = None
    if request.username:
        user = await crud.get_user_by_username(db, request.username)
    elif request.user_id:
        user = await crud.get_user_by_id(db, request.user_id)
    
    if not user:
        raise HTTPException(404, "User not found")
    
    new_balance = await crud.update_user_balance(db, user.id, request.amount_stars)
    return BalanceResponse(balance_stars=new_balance, username=user.username)


from core.schemas import AdminCreateUserRequest, RegisterResponse

@router.post("/create-first-user", response_model=RegisterResponse)
async def create_first_user(
    request: AdminCreateUserRequest,
    x_admin_uuid: str = Header(alias="X-Admin-UUID"),
    db: AsyncSession = Depends(get_db)
):
    """Создать первого пользователя без инвайта (только для настройки)"""
    if x_admin_uuid != ADMIN_UUID:
        raise HTTPException(403, "Invalid admin UUID")
    
    # Проверяем что пользователей ещё нет
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    if len(users) > 0:
        raise HTTPException(400, "Пользователи уже существуют. Используйте /auth/register")
    
    # Создаём пользователя
    user = await crud.create_user(db, request.username, request.password, invite_code="admin")
    
    # Создаём прокси услугу
    await crud.create_proxy_service(db, user.id)
    
    # Начисляем тестовые звёзды
    await crud.update_user_balance(db, user.id, 100)
    
    return {"message": "First user created", "user_id": user.id}
