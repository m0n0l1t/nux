from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from db import crud
from services.bot.handlers.start import cmd_start
from services.bot.keyboards import get_main_menu_kb
from services.bot.utils.db_helpers import get_db_session

router = Router()

@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    async with get_db_session() as db:
        user = await crud.get_user_by_telegram_id(db, message.from_user.id)
        if not user:
            await cmd_start(message, state)
            return
        await message.answer(
            f"👋 <b>Главное меню</b>\nПользователь: {user.username}",
            parse_mode="HTML",
            reply_markup=get_main_menu_kb()
        )
    await state.clear()

@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📱 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()