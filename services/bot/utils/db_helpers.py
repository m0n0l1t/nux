from contextlib import asynccontextmanager
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db import models
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_db_session():
    """Контекстный менеджер для сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise

async def get_user_by_telegram_id(telegram_id: int, db):
    """Получить пользователя по telegram_id"""
    result = await db.execute(
        select(models.User).where(models.User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()