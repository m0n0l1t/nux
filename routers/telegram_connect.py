from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
from db.database import get_db
from core.auth import get_current_user
from db.models import User, TelegramConnectCode
from sqlalchemy import select
from db import crud

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/connect")
async def generate_connect_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерирует код для привязки Telegram аккаунта"""
    # Проверяем, не привязан ли уже Telegram
    if current_user.telegram_id:
        raise HTTPException(400, "Telegram уже привязан к вашему аккаунту")
    
    # Генерируем код
    code = str(uuid.uuid4())[:8].upper()  # Короткий код, например: A1B2C3D4
    
    connect_code = TelegramConnectCode(
        code=code,
        user_id=current_user.id
    )
    
    db.add(connect_code)
    await db.commit()
    await db.refresh(connect_code)
    
    return {
        "code": code,
        "expires_in": 300,  # 5 минут
        "instruction": f"Отправьте этот код боту для привязки аккаунта"
    }


@router.get("/connect/{code}")
async def verify_connect_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Проверяет код и привязывает Telegram (вызывается из бота)"""
    result = await db.execute(
        select(TelegramConnectCode)
        .where(TelegramConnectCode.code == code)
        .where(TelegramConnectCode.is_used == False)
    )
    connect_code = result.scalar_one_or_none()
    
    if not connect_code:
        raise HTTPException(404, "Неверный или использованный код")
    
    # Проверяем не истёк ли код (5 минут)
    if (datetime.utcnow() - connect_code.created_at).total_seconds() > 300:
        raise HTTPException(400, "Код истёк")
    
    user = await crud.get_user_by_id(db, connect_code.user_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    
    # Помечаем код как использованный
    connect_code.is_used = True
    connect_code.used_at = datetime.utcnow()
    await db.commit()
    
    return {
        "user_id": user.id,
        "username": user.username,
        "message": "Код подтверждён"
    }
