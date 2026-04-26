from contextlib import asynccontextmanager
from db.database import AsyncSessionLocal
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
