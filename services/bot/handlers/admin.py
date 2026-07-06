from aiogram import Router
from aiogram.types import CallbackQuery

import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == "balance_bot")
async def show_balance_bot(callback: CallbackQuery):
    # Получаем баланс Stars
    star_amount = await callback.message.bot.get_my_star_balance()

    # Отправляем ответ пользователю
    await callback.message.answer(f"Текущий баланс бота: {star_amount.amount} ⭐️")