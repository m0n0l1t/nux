from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from services.bot.states import AuthState
from services.bot.keyboards import get_main_menu_kb, get_back_kb
from services.bot.utils.db_helpers import get_db_session, get_user_by_telegram_id, logger
from db import crud
from db.crud import create_user_from_telegram, create_proxy_service, get_user_by_id

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Главная команда — проверяет авторизацию"""
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(message.from_user.id, db)

        if user:
            await message.answer(
                f"👋 <b>С возвращением, {user.username}!</b>\n\n"
                f"💰 Баланс: <b>{user.balance_stars:.1f} ⭐️</b>\n"
                f"📅 Аккаунт создан: {user.created_at.strftime('%d.%m.%Y')}\n\n"
                f"Используйте меню ниже 👇",
                parse_mode="HTML",
                reply_markup=get_main_menu_kb()
            )
            await state.clear()
        else:
            kb = InlineKeyboardBuilder()
            kb.button(text="🔑 У меня есть инвайт", callback_data="auth_invite")
            kb.button(text="ℹ️ Как получить инвайт?", callback_data="auth_help")
            kb.adjust(1)
            await message.answer(
                f"👋 <b>Добро пожаловать в NuxClub!</b>\n\n"
                f"🔐 Для доступа к услугам необходим инвайт-код.\n\n"
                f"Выберите действие:",
                parse_mode="HTML",
                reply_markup=kb.as_markup()
            )


@router.callback_query(lambda c: c.data == "auth_invite")
async def auth_invite_handler(callback: CallbackQuery, state: FSMContext):
    """Начинаем процесс регистрации через инвайт"""
    await callback.message.edit_text(
        "🔑 <b>Регистрация</b>\n\n"
        "Введите ваш <b>инвайт-код</b>:\n"
        "<i>(его вы получали при регистрации на сайте или от друга)</i>",
        parse_mode="HTML"
    )
    await state.set_state(AuthState.waiting_for_invite_code)
    await callback.answer()


@router.callback_query(lambda c: c.data == "auth_help")
async def auth_help_handler(callback: CallbackQuery):
    """Помощь по получению инвайта"""
    await callback.message.edit_text(
        "ℹ️ <b>Как начать?</b>\n\n"
        "1️⃣ Получите инвайт-код от друга или администратора\n"
        "2️⃣ Введите инвайт здесь — вы зарегистрируетесь автоматически\n"
        "3️⃣ (Опционально) Зарегистрируйтесь на сайте с тем же инвайтом,\n"
        "   чтобы установить логин и пароль для веб-кабинета\n\n"
        "💡 Один инвайт = один пользователь!",
        parse_mode="HTML",
        reply_markup=get_back_kb("back_to_start")
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    """Возврат к начальному экрану"""
    await state.clear()
    await cmd_start(callback.message, state)
    await callback.answer()


@router.message(AuthState.waiting_for_invite_code)
async def process_invite_code(message: Message, state: FSMContext):
    """Обработка введённого инвайт-кода"""
    invite_code = message.text.strip()
    async with get_db_session() as db:
        invite = await crud.get_invite_by_code(db, invite_code)
        if not invite or (invite.expires_at and invite.expires_at < datetime.utcnow()):
            kb = InlineKeyboardBuilder()
            kb.button(text="🔄 Попробовать снова", callback_data="auth_invite")
            kb.button(text="🏠 На главную", callback_data="back_to_start")
            kb.adjust(1)
            await message.answer(
                "❌ <b>Неверный или истёкший инвайт-код</b>\n\n"
                "Проверьте правильность и попробуйте снова.",
                parse_mode="HTML",
                reply_markup=kb.as_markup()
            )
            return

        if invite.used_by_user_id:
            existing_user = await get_user_by_id(invite.used_by_user_id, db)
            if existing_user and existing_user.telegram_id == message.from_user.id:
                await message.answer(
                    f"✅ <b>Вы уже зарегистрины как {existing_user.username}!</b>\n\n"
                    f"💰 Баланс: <b>{existing_user.balance_stars:.1f} ⭐️</b>",
                    parse_mode="HTML",
                    reply_markup=get_main_menu_kb()
                )
                await state.clear()
                return
            else:
                await message.answer(
                    "❌ <b>Этот инвайт-код уже использован другим пользователем</b>\n\n"
                    "Используйте другой код или обратитесь к администратору.",
                    parse_mode="HTML",
                    reply_markup=get_back_kb("back_to_start")
                )
                return

        existing = await get_user_by_telegram_id(message.from_user.id, db)
        if existing:
            await message.answer(
                f"✅ <b>Вы уже зарегистрированы!</b>\n\n"
                f"👤 Пользователь: <b>{existing.username}</b>\n"
                f"💰 Баланс: <b>{existing.balance_stars:.1f} ⭐️</b>\n\n"
                f"Теперь используйте меню 👇",
                parse_mode="HTML",
                reply_markup=get_main_menu_kb()
            )
            await state.clear()
            return

        try:
            user = await create_user_from_telegram(db, message.from_user.id, invite_code)
            invite.used_by_user_id = user.id
            invite.used_at = datetime.utcnow()
            await db.commit()
            await create_proxy_service(db, user.id)
            await message.answer(
                f"🎉 <b>Регистрация успешна!</b>\n\n"
                f"👤 Ваш ID: <b>{user.id}</b>\n"
                f"💰 Баланс: <b>{user.balance_stars:.1f} ⭐️</b>\n\n"
                f"💡 Теперь вы можете зарегистрироваться на сайте с этим же инвайт-кодом,\n"
                f"чтобы установить логин и пароль.\n\n"
                f"Используйте меню 👇",
                parse_mode="HTML",
                reply_markup=get_main_menu_kb()
            )
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await message.answer(
                "❌ <b>Ошибка при регистрации</b>\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=get_back_kb("back_to_start")
            )
        await state.clear()