from aiogram import Router
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from services.bot.keyboards import get_main_menu_kb
from services.bot.utils.db_helpers import get_db_session, get_user_by_telegram_id
from db import crud

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: CallbackQuery):
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return
        text = (
            f"💰 <b>Ваш баланс</b>\n\n"
            f"⭐️ Звёзды: <b>{user.balance_stars:.1f}</b>\n\n"
            f"💡 1 NuxGuard = 3 ⭐️/мес\n"
            f"💡 NuxTunnel бесплатен при NuxGuard"
        )
        kb = InlineKeyboardBuilder()
        kb.button(text="⭐️ Пополнить баланс", callback_data="topup")
        kb.button(text="🔙 Назад", callback_data="back_to_menu")
        kb.adjust(1)
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(lambda c: c.data == "tariffs")
async def show_tariffs(callback: CallbackQuery):
    text = (
        f"📋 <b>Тарифы NuxClub</b>\n\n"
        f"🔐 <b>NuxGuard</b>\n"
        f"• Безлимитный тариф\n"
        f"• Стоимость: 3 ⭐️/мес\n"
        f"• Без ограничений по трафику\n\n"
        f"📡 <b>NuxTunnel</b>\n"
        f"• Бесплатно при наличии NuxGuard\n\n"
        f"💡 Оплата продлевает услугу автоматически"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐️ Пополнить баланс", callback_data="topup")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(1)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(lambda c: c.data == "topup")
async def topup_prompt(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐️ 3 звезды (1 услуга)", callback_data="topup_3")
    kb.button(text="⭐️ 6 звезд (2 услуги)", callback_data="topup_6")
    kb.button(text="⭐️ 9 звезд (3 услуги)", callback_data="topup_9")
    kb.button(text="⭐️ 30 звезд (10 услуг)", callback_data="topup_30")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(2)
    await callback.message.edit_text(
        "⭐️ <b>Пополнение баланса</b>\n\nВыберите количество звёзд:",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("topup_") and c.data != "topup")
async def topup_invoice(callback: CallbackQuery, bot):
    amount = int(callback.data.split("_")[1])
    try:
        prices = [LabeledPrice(label=f"⭐️ {amount} Stars", amount=amount)]
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Пополнение баланса — {amount} ⭐️",
            description=f"Пополнение баланса на {amount} звёзд для оплаты услуг VPN",
            payload=f"topup_{amount}",
            provider_token="",
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        await callback.answer("❌ Ошибка создания инвойса", show_alert=True)
    await callback.answer()

@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)

@router.message(lambda m: m.successful_payment is not None)
async def on_successful_payment(message: Message):
    payment = message.successful_payment
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(message.from_user.id, db)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return
        try:
            amount = int(payment.invoice_payload.split("_")[1])
        except:
            await message.answer("❌ Ошибка обработки платежа")
            return
        await crud.create_payment_record(
            db, user.id, amount,
            telegram_payment_id=payment.telegram_payment_charge_id,
            status="success",
            description="Пополнение через Telegram Stars"
        )
        new_balance = await crud.update_user_balance(db, user.id, amount)
        await message.answer(
            f"✅ <b>Оплата успешна!</b>\n\n"
            f"⭐️ Зачислено: <b>{amount}</b> звёзд\n"
            f"💰 Новый баланс: <b>{new_balance:.1f}</b> звёзд",
            parse_mode="HTML",
            reply_markup=get_main_menu_kb()
        )