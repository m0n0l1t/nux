from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.bot.keyboards import get_back_kb

router = Router()

@router.callback_query(lambda c: c.data == "instructions")
async def show_instructions(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="📡 NuxTunnel", callback_data="help_tunnel")
    kb.button(text="🔐 NuxGuard", callback_data="help_guard")
    kb.button(text="⭐️ Оплата", callback_data="help_payment")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(2)
    await callback.message.edit_text(
        "📖 <b>Инструкции</b>\n\nВыберите тему:",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "help_tunnel")
async def help_tunnel(callback: CallbackQuery):
    text = (
        "📡 <b>NuxTunnel (Прокси)</b>\n\n"
        "<b>Как подключить:</b>\n"
        "1️⃣ Войдите в личный кабинет\n"
        "2️⃣ В разделе 'NuxTunnel' нажмите 'Подключиться'\n"
        "3️⃣ Откроется Telegram с предложением подключить прокси\n"
        "4️⃣ Нажмите 'Подключить' — готово!\n\n"
        "<b>Через бота:</b>\n"
        "1️⃣ /menu → '📡 NuxTunnel'\n"
        "2️⃣ Скопируйте ссылку и перейдите\n\n"
        "<b>Важно:</b>\n"
        "✅ Бесплатен при наличии NuxGuard\n"
        "✅ При регистрации — 7 дней бесплатно\n"
        "❌ Без NuxGuard прокси отключается"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_kb("instructions"))
    await callback.answer()

@router.callback_query(lambda c: c.data == "help_guard")
async def help_guard(callback: CallbackQuery):
    text = (
        "🔐 <b>NuxGuard (WireGuard)</b>\n\n"
        "<b>Как создать:</b>\n"
        "1️⃣ Войдите в личный кабинет или бота\n"
        "2️⃣ Нажмите '➕ Создать'\n"
        "3️⃣ Введите название и скачайте конфиг\n\n"
        "<b>Как подключить:</b>\n"
        "• Windows/macOS/Linux: WireGuard клиент\n"
        "• Android/iOS: AmneziaWG или WireGuard приложение\n"
        "• Импортируйте .conf файл и подключитесь\n\n"
        "<b>Стоимость:</b>\n"
        "💰 3 ⭐️/мес за услугу\n"
        "✅ Безлимитный трафик\n"
        "✅ Автопродление при наличии баланса"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_kb("instructions"))
    await callback.answer()

@router.callback_query(lambda c: c.data == "help_payment")
async def help_payment(callback: CallbackQuery):
    text = (
        "⭐️ <b>Оплата и баланс</b>\n\n"
        "<b>Как пополнить:</b>\n"
        "1️⃣ /menu → '⭐️ Пополнить'\n"
        "2️⃣ Выберите пакет звёзд\n"
        "3️⃣ Оплатите через Telegram\n\n"
        "<b>Автопродление:</b>\n"
        "• Проверка каждые 6 часов\n"
        "• Баланс ≥ 3 ⭐️ — услуга продлевается\n"
        "• Баланс = 0 ⭐️ — услуга деактивируется\n\n"
        "<b>Тарифы:</b>\n"
        "🔐 NuxGuard: 3 ⭐️/мес\n"
        "📡 NuxTunnel: бесплатно (при NuxGuard)"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_kb("instructions"))
    await callback.answer()