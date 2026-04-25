import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from db.database import get_db, Base
from db import models  # Импорт моделей
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from services.bot import dp, bot

# Тестовая БД — используйте in-memory SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def dispatcher():
    # Используем MemoryStorage для тестов, чтобы не трогать Redis
    storage = MemoryStorage()
    test_dispatcher = Dispatcher(storage=storage)
    # Переносим все хендлеры
    test_dispatcher.include_router(dp.router)
    return test_dispatcher

@pytest.fixture
def mock_bot():
    bot.session.close()  # Закрываем реальную сессию бота
    return MagicMock(spec=bot)  # Мокаем все методы бота