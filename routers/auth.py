from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from core.schemas import UserRegisterRequest, UserLoginRequest, LinkCredentialsRequest, TokenResponse, RegisterResponse
from datetime import datetime

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=RegisterResponse)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    invite = await crud.get_invite_by_code(db, request.invite_code)
    if not invite or invite.used_by_user_id:
        raise HTTPException(400, "Invalid or already used invite")
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invite expired")
    if await crud.get_user_by_username(db, request.username):
        raise HTTPException(400, "Username exists")
    user = await crud.create_user(db, request.username, request.password, request.invite_code)
    invite.used_by_user_id = user.id
    invite.used_at = datetime.utcnow()
    await db.commit()
    await crud.create_proxy_service(db, user.id)
    return {"message": "Registered", "user_id": user.id}

@router.post("/link-credentials", response_model=RegisterResponse)
async def link_credentials(
    request: LinkCredentialsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Привязывает логин/пароль к пользователю, зарегистрированному через Telegram бота.
    Не создаёт нового пользователя — использует существующего по telegram_id."""
    invite = await crud.get_invite_by_code(db, request.invite_code)
    if not invite:
        raise HTTPException(400, "Invalid invite code")
    # Инвайт может быть уже использован — это нормально, если это тот же пользователь
    
    # Находим пользователя по invite_code (должен быть зарегистрирован через бота)
    from sqlalchemy import select
    from db.models import User
    result = await db.execute(
        select(User).where(User.invite_code_used == request.invite_code)
    )
    telegram_user = result.scalar_one_or_none()
    
    if not telegram_user or not telegram_user.telegram_registered:
        raise HTTPException(400, "User not found. Please register via Telegram bot first.")
    
    if telegram_user.telegram_id is None:
        raise HTTPException(400, "Telegram account not linked. Please use the bot first.")
    
    # Привязываем логин/пароль
    user = await crud.link_credentials_to_telegram_user(
        db, telegram_user.telegram_id, request.username, request.password, request.invite_code
    )
    
    if not user:
        raise HTTPException(400, "Failed to link credentials. Username may be taken.")
    
    # Если инвайт ещё не помечен как использованный, помечаем
    if not invite.used_by_user_id:
        invite.used_by_user_id = user.id
        invite.used_at = datetime.utcnow()
        await db.commit()
    
    # Создаём proxy service если его нет
    proxy = await crud.get_proxy_service(db, user.id)
    if not proxy:
        await crud.create_proxy_service(db, user.id)
    
    return {"message": "Credentials linked successfully", "user_id": user.id}

@router.post("/token", response_model=TokenResponse)
async def login(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    user = await crud.authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    from core.auth import create_access_token
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
