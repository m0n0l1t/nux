import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vpn_app.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Применяем миграции Alembic вместо create_all"""
    import subprocess
    import sys
    import asyncio

    # Путь к python в venv
    venv_python = sys.executable

    try:
        # Запускаем alembic upgrade head
        process = await asyncio.create_subprocess_exec(
            venv_python, "-m", "alembic", "upgrade", "head",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            import logging
            logging.getLogger(__name__).info("✅ Alembic migrations applied")
        else:
            import logging
            logging.getLogger(__name__).error(f"Alembic error: {stderr.decode()}")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Alembic not available, using create_all fallback: {e}")
        # Fallback: создаём таблицы если alembic не работает
        from database import engine, Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)