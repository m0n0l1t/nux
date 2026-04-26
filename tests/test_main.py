import pytest
from httpx import AsyncClient
from main import app
from db.database import get_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from aiogram.fsm.storage.memory import MemoryStorage

# ---------- Настройка тестовой БД ----------
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Переопределяем зависимость get_db
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# ---------- Фикстуры ----------
@pytest.fixture(autouse=True)
async def setup_database():
    """Создаёт таблицы перед каждым тестом и удаляет после."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# ---------- Тесты ----------
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data

async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    # Если корень возвращает что-то (редирект или HTML)
    assert response.headers["content-type"] == "text/html; charset=utf-8"

async def test_docs_available(client: AsyncClient):
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()