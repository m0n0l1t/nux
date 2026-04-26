# bot/main.py
import asyncio

from aiogram import Bot, Dispatcher

from services.bot.handlers import register_all_handlers
from db.database import engine, Base
from services.bot.config import BOT_TOKEN


async def init_bot() -> Dispatcher:
    """Инициализирует и настраивает бота, возвращает Dispatcher"""
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    register_all_handlers(dp)
    await _init_db()  # опционально
    return bot, dp

async def _init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def start_polling():
    """Запускает поллинг (для отдельного процесса)"""
    dp = await init_bot()
    await dp.start_polling(dp.bot)

def run_bot():
    """Синхронная обёртка для удобного вызова из внешнего кода"""
    asyncio.run(start_polling())

if __name__ == "__main__":
    run_bot()