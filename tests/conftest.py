import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from db.database import get_db, Base
from db import models  # Импорт моделей

# Тестовая БД — используйте in-memory SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


engine = create_async_engine(TEST_DATABASE_URL, echo=False)
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
    async with TestingSessionLocal() as session:
        admin = models.User(username="admin", telegram_registered=False, is_active=True, invite_quota=100, balance_stars=0)
        session.add(admin)
        await session.commit()
        invite = models.Invite(code="VALID_INVITE", creator_user_id=admin.id)
        session.add(invite)
        await session.commit()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Асинхронный HTTP-клиент для тестирования FastAPI."""
    transport = ASGITransport(app=app)  # создаём транспорт
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def auth_headers(client):
    # Создаём временного пользователя
    reg_payload = {
        "username": "temp_user",
        "password": "temp_pass",
        "invite_code": "VALID_INVITE"
    }
    await client.post("/auth/register", json=reg_payload)
    login_resp = await client.post("/auth/token", json={"username": "temp_user", "password": "temp_pass"})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}