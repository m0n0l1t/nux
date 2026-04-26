from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import httpx
import logging

from services.bot.states import ConnectState
from services.bot.keyboards import get_main_menu_kb
from services.bot.utils.db_helpers import get_db_session
from db import models
from sqlalchemy import select

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("connect"))
async def cmd_connect(message: Message, state: FSMContext):
    async with get_db_session() as db:
        result = await db.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            await message.answer(
                f"✅ Telegram уже привязан к аккаунту <b>{user.username}</b>",
                parse_mode="HTML"
            )
            return
    await message.answer(
        "📱 <b>Привязка аккаунта</b>\n\nВведите код, полученный на сайте:",
        parse_mode="HTML"
    )
    await state.set_state(ConnectState.waiting_for_code)

@router.message(ConnectState.waiting_for_code)
async def process_connect_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:8000/telegram/connect/{code}")
            if response.status_code != 200:
                await message.answer(
                    "❌ Неверный или истёкший код.\n\nПопробуйте снова или /cancel"
                )
                return
            data = response.json()
            user_id = data["user_id"]
            username = data["username"]
        async with get_db_session() as db:
            result = await db.execute(select(models.User).where(models.User.id == user_id))
            user = result.scalar_one_or_none()
            if user and not user.telegram_id:
                user.telegram_id = message.from_user.id
                await db.commit()
                await message.answer(
                    f"✅ <b>Telegram привязан к {username}!</b>\n\n"
                    f"💰 Баланс: <b>{user.balance_stars:.1f} ⭐️</b>\n\n"
                    f"Используйте /menu",
                    parse_mode="HTML",
                    reply_markup=get_main_menu_kb()
                )
                await state.clear()
            else:
                await message.answer("❌ Ошибка привязки. Пользователь не найден или уже привязан")
    except Exception as e:
        logger.error(f"Connect error: {e}")
        await message.answer("❌ Ошибка привязки. Попробуйте позже")