import asyncio
import os
import logging
from contextlib import asynccontextmanager
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from sqlalchemy import select
from datetime import datetime
from db import models
from db.crud import create_proxy_service, create_user_from_telegram
from db.database import engine, Base, AsyncSessionLocal

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logger = logging.getLogger(__name__)


# ========== КОНТЕКСТНЫЙ МЕНЕДЖЕР БД ==========

@asynccontextmanager
async def get_db_session():
    """Контекстный менеджер для работы с БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise


# ========== СОСТОЯНИЯ ==========

class AuthState(StatesGroup):
    waiting_for_invite_code = State()
    waiting_for_username = State()
    waiting_for_password = State()


class CreateWGState(StatesGroup):
    waiting_for_name = State()


class ConnectState(StatesGroup):
    waiting_for_code = State()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def get_user_by_telegram_id(telegram_id: int, db):
    result = await db.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


def get_main_menu_kb():
    """Создаёт главное меню с эмодзи и красивым оформлением"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Баланс", callback_data="balance")
    kb.button(text="⭐️ Пополнить", callback_data="topup")
    kb.button(text="📡 NuxTunnel", callback_data="proxy")
    kb.button(text="🔐 NuxGuard", callback_data="wg_list")
    kb.button(text="➕ Создать", callback_data="wg_create")
    kb.button(text="📖 Инструкции", callback_data="instructions")
    kb.button(text="🎫 Инвайты", callback_data="invites")
    kb.button(text="✨ Создать инвайт", callback_data="create_invite")
    kb.button(text="📋 Тарифы", callback_data="tariffs")
    kb.adjust(2)  # 2 кнопки в ряд
    return kb.as_markup()


def get_back_kb(callback_data: str = "back_to_menu"):
    """Клавиатура с кнопкой Назад"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data=callback_data)
    return kb.as_markup()


# ========== КОМАНДЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Главная команда — проверяет авторизацию"""
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(message.from_user.id, db)
        
        if user:
            # Пользователь авторизован
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
            # Пользователь не авторизован
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


@dp.callback_query(lambda c: c.data == "auth_invite")
async def auth_invite_handler(callback: types.CallbackQuery, state: FSMContext):
    """Начинаем процесс регистрации через инвайт"""
    await callback.message.edit_text(
        "🔑 <b>Регистрация</b>\n\n"
        "Введите ваш <b>инвайт-код</b>:\n"
        "<i>(его вы получали при регистрации на сайте или от друга)</i>",
        parse_mode="HTML"
    )
    await state.set_state(AuthState.waiting_for_invite_code)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "auth_help")
async def auth_help_handler(callback: types.CallbackQuery):
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


@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к начальному экрану"""
    await state.clear()
    await cmd_start(callback.message, state)
    await callback.answer()


@dp.message(AuthState.waiting_for_invite_code)
async def process_invite_code(message: types.Message, state: FSMContext):
    """Обрабатываем введённый инвайт-код — регистрируем пользователя"""
    invite_code = message.text.strip()

    async with get_db_session() as db:
        # Проверяем инвайт
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

        # Проверяем, не использован ли уже инвайт
        if invite.used_by_user_id:
            # Инвайт уже использован — проверяем, может это тот же пользователь
            result = await db.execute(
                select(models.User).where(models.User.id == invite.used_by_user_id)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user and existing_user.telegram_id == message.from_user.id:
                # Этот пользователь уже зарегистриен
                await message.answer(
                    f"✅ <b>Вы уже зарегистрины как {existing_user.username}!</b>\n\n"
                    f"💰 Баланс: <b>{existing_user.balance_stars:.1f} ⭐️</b>",
                    parse_mode="HTML",
                    reply_markup=get_main_menu_kb()
                )
                await state.clear()
                return
            else:
                # Инвайт уже использован другим пользователем
                await message.answer(
                    "❌ <b>Этот инвайт-код уже использован другим пользователем</b>\n\n"
                    "Используйте другой код или обратитесь к администратору.",
                    parse_mode="HTML",
                    reply_markup=get_back_kb("back_to_start")
                )
                return

        # Проверяем, не зарегистрирован ли пользователь с таким telegram_id
        existing = await get_user_by_telegram_id(db, message.from_user.id)
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

        # Регистрируем нового пользователя
        try:
            user = await create_user_from_telegram(db, message.from_user.id, invite_code)
            
            # Помечаем инвайт как использованный
            invite.used_by_user_id = user.id
            invite.used_at = datetime.utcnow()
            await db.commit()
            
            # Создаём proxy service для нового пользователя
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


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    """Главное меню"""
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(message.from_user.id, db)
        
        if not user:
            await cmd_start(message, state)
            return
        
        await message.answer(
            f"👋 <b>Главное меню</b>\n"
            f"Пользователь: {user.username}",
            parse_mode="HTML",
            reply_markup=get_main_menu_kb()
        )
    await state.clear()


@dp.message(Command("connect"))
async def cmd_connect(message: types.Message, state: FSMContext):
    """Привязка аккаунта через код с сайта"""
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(message.from_user.id, db)
        if user:
            await message.answer(
                f"✅ Telegram уже привязан к аккаунту <b>{user.username}</b>",
                parse_mode="HTML"
            )
            return
    
    await message.answer(
        "📱 <b>Привязка аккаунта</b>\n\n"
        "Введите код, полученный на сайте:",
        parse_mode="HTML"
    )
    await state.set_state(ConnectState.waiting_for_code)


@dp.message(ConnectState.waiting_for_code)
async def process_connect_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:8000/telegram/connect/{code}")
            
            if response.status_code != 200:
                await message.answer(
                    "❌ Неверный или истёкший код.\n\n"
                    "Попробуйте снова или /cancel",
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


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Операция отменена. Используйте /menu")


# ========== ГЛАВНОЕ МЕНЮ ==========

async def show_menu(message: types.Message):
    await message.answer(
        "📱 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb()
    )


# ========== БАЛАНС ==========

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: types.CallbackQuery):
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


# ========== ТАРИФЫ ==========

@dp.callback_query(lambda c: c.data == "tariffs")
async def show_tariffs(callback: types.CallbackQuery):
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


# ========== ПОПОЛНЕНИЕ ==========

@dp.callback_query(lambda c: c.data == "topup")
async def topup_prompt(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐️ 3 звезды (1 услуга)", callback_data="topup_3")
    kb.button(text="⭐️ 6 звезд (2 услуги)", callback_data="topup_6")
    kb.button(text="⭐️ 9 звезд (3 услуги)", callback_data="topup_9")
    kb.button(text="⭐️ 30 звезд (10 услуг)", callback_data="topup_30")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(2)
    
    await callback.message.edit_text(
        "⭐️ <b>Пополнение баланса</b>\n\n"
        "Выберите количество звёзд:",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("topup_") and c.data != "topup")
async def topup_invoice(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])
    
    try:
        from aiogram.types import LabeledPrice
        
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


@dp.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)


@dp.message(lambda m: m.successful_payment is not None)
async def on_successful_payment(message: types.Message):
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
        
        payment_record = await crud.create_payment_record(
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


# ========== НАЗАД В МЕНЮ ==========

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📱 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()


# ========== ПРОКСИ ==========

@dp.callback_query(lambda c: c.data == "proxy")
async def show_proxy(callback: types.CallbackQuery):
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return
        
        proxy = await crud.get_proxy_service(db, user.id)
        if not proxy:
            await callback.message.answer(
                "❌ Услуга NuxTunnel не найдена",
                reply_markup=get_back_kb()
            )
            await callback.answer()
            return
        
        days_left = (proxy.expiration_date - datetime.utcnow()).days
        text = (
            f"📡 <b>NuxTunnel</b>\n\n"
            f"📛 Название: {proxy.name}\n"
            f"⏳ Осталось дней: <b>{days_left}</b>\n"
            f"🔗 Ссылка: <code>{proxy.proxy_link}</code>"
        )
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ========== СПИСОК NUXGUARD ==========

@dp.callback_query(lambda c: c.data == "wg_list")
async def list_wg(callback: types.CallbackQuery):
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return
        
        services = await crud.get_wireguard_services_by_user(db, user.id)
        if not services:
            await callback.message.answer(
                "У вас нет услуг NuxGuard. Создайте первую через меню.",
                reply_markup=get_back_kb()
            )
            await callback.answer()
            return
        
        for s in services:
            days_left = (s.expiration_date - datetime.utcnow()).days
            text = (
                f"🔐 <b>{s.name}</b>\n"
                f"⏳ Осталось дней: <b>{days_left}</b>\n"
                f"🌐 Адрес: <code>{s.address}</code>\n"
                f"🔑 Ключ: <code>{s.public_key}</code>"
            )
            kb = InlineKeyboardBuilder()
            kb.button(text="📥 Скачать конфиг", callback_data=f"download_{s.id}")
            kb.button(text="🗑 Удалить", callback_data=f"delete_wg_{s.id}")
            kb.adjust(2)
            
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


# ========== СКАЧИВАНИЕ КОНФИГА ==========

@dp.callback_query(lambda c: c.data.startswith("download_"))
async def download_config(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        if not user:
            await callback.answer("Авторизуйтесь", show_alert=True)
            return
        
        svc = await crud.get_wireguard_service(db, service_id, user.id)
        if not svc:
            await callback.answer("Услуга не найдена", show_alert=True)
            return
        
        from routers.wireguard import generate_wireguard_config
        config = generate_wireguard_config(svc)
        
        file_data = config.encode('utf-8')
        await callback.message.answer_document(
            BufferedInputFile(file_data, filename=f"nuxguard_{svc.name}.conf")
        )
    await callback.answer()


# ========== УДАЛЕНИЕ NUXGUARD ==========

@dp.callback_query(lambda c: c.data.startswith("delete_wg_"))
async def delete_wg(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[2])
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        if not user:
            await callback.answer("Авторизуйтесь", show_alert=True)
            return
        
        svc = await crud.get_wireguard_service(db, service_id, user.id)
        if svc:
            await crud.delete_wireguard_service(db, svc)
            await callback.answer("✅ Услуга удалена", show_alert=True)
            try:
                await callback.message.delete()
            except:
                pass
        else:
            await callback.answer("Услуга не найдена", show_alert=True)
    await callback.answer()


# ========== СОЗДАНИЕ NUXGUARD ==========

@dp.callback_query(lambda c: c.data == "wg_create")
async def create_wg_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "➕ <b>Создание NuxGuard</b>\n\n"
        "Введите название услуги:\n"
        "<i>(например, 'Мой сервер')</i>",
        parse_mode="HTML"
    )
    await state.set_state(CreateWGState.waiting_for_name)
    await callback.answer()


@dp.message(CreateWGState.waiting_for_name)
async def create_wg_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз.")
        return
    
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(message.from_user.id, db)
        if not user:
            await message.answer("Ошибка авторизации. Используйте /start")
            await state.clear()
            return
        
        try:
            service = await crud.create_wireguard_service(db, user.id, name)
            await message.answer(
                f"✅ <b>Услуга NuxGuard '{name}' создана!</b>\n\n"
                f"🌐 Адрес: <code>{service.address}</code>\n"
                f"🔑 Ключ: <code>{service.public_key}</code>",
                parse_mode="HTML",
                reply_markup=get_main_menu_kb()
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка создания: {str(e)}")
    await state.clear()


# ========== ИНСТРУКЦИИ ==========

@dp.callback_query(lambda c: c.data == "instructions")
async def show_instructions(callback: types.CallbackQuery):
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


@dp.callback_query(lambda c: c.data == "help_tunnel")
async def help_tunnel(callback: types.CallbackQuery):
    text = (
        f"📡 <b>NuxTunnel (Прокси)</b>\n\n"
        f"<b>Как подключить:</b>\n"
        f"1️⃣ Войдите в личный кабинет\n"
        f"2️⃣ В разделе 'NuxTunnel' нажмите 'Подключиться'\n"
        f"3️⃣ Откроется Telegram с предложением подключить прокси\n"
        f"4️⃣ Нажмите 'Подключить' — готово!\n\n"
        f"<b>Через бота:</b>\n"
        f"1️⃣ /menu → '📡 NuxTunnel'\n"
        f"2️⃣ Скопируйте ссылку и перейдите\n\n"
        f"<b>Важно:</b>\n"
        f"✅ Бесплатен при наличии NuxGuard\n"
        f"✅ При регистрации — 7 дней бесплатно\n"
        f"❌ Без NuxGuard прокси отключается"
    )
    
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_kb("instructions"))
    await callback.answer()


@dp.callback_query(lambda c: c.data == "help_guard")
async def help_guard(callback: types.CallbackQuery):
    text = (
        f"🔐 <b>NuxGuard (WireGuard)</b>\n\n"
        f"<b>Как создать:</b>\n"
        f"1️⃣ Войдите в личный кабинет или бота\n"
        f"2️⃣ Нажмите '➕ Создать'\n"
        f"3️⃣ Введите название и скачайте конфиг\n\n"
        f"<b>Как подключить:</b>\n"
        f"• Windows/macOS/Linux: WireGuard клиент\n"
        f"• Android/iOS: AmneziaWG или WireGuard приложение\n"
        f"• Импортируйте .conf файл и подключитесь\n\n"
        f"<b>Стоимость:</b>\n"
        f"💰 3 ⭐️/мес за услугу\n"
        f"✅ Безлимитный трафик\n"
        f"✅ Автопродление при наличии баланса"
    )
    
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_kb("instructions"))
    await callback.answer()


@dp.callback_query(lambda c: c.data == "help_payment")
async def help_payment(callback: types.CallbackQuery):
    text = (
        f"⭐️ <b>Оплата и баланс</b>\n\n"
        f"<b>Как пополнить:</b>\n"
        f"1️⃣ /menu → '⭐️ Пополнить'\n"
        f"2️⃣ Выберите пакет звёзд\n"
        f"3️⃣ Оплатите через Telegram\n\n"
        f"<b>Автопродление:</b>\n"
        f"• Проверка каждые 6 часов\n"
        f"• Баланс ≥ 3 ⭐️ — услуга продлевается\n"
        f"• Баланс = 0 ⭐️ — услуга деактивируется\n\n"
        f"<b>Тарифы:</b>\n"
        f"🔐 NuxGuard: 3 ⭐️/мес\n"
        f"📡 NuxTunnel: бесплатно (при NuxGuard)"
    )
    
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_kb("instructions"))
    await callback.answer()


# ========== ИНВАЙТЫ ==========

@dp.callback_query(lambda c: c.data == "invites")
async def list_invites(callback: types.CallbackQuery):
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return
        
        invites = await crud.get_invites_by_creator(db, user.id)
        if not invites:
            await callback.message.answer(
                "У вас нет созданных инвайтов.",
                reply_markup=get_back_kb()
            )
            return
        
        for inv in invites:
            used = "✅ Использован" if inv.used_by_user_id else "🟢 Не использован"
            text = (
                f"🎫 <b>Код:</b> <code>{inv.code}</code>\n"
                f"{used}\n"
                f"📅 Создан: {inv.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(lambda c: c.data == "create_invite")
async def create_invite_cmd(callback: types.CallbackQuery):
    async with get_db_session() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        if not user:
            await callback.answer("Авторизуйтесь", show_alert=True)
            return
        
        invites = await crud.get_invites_by_creator(db, user.id)
        unused = [inv for inv in invites if inv.used_by_user_id is None]
        if user.invite_quota is not None and len(unused) >= user.invite_quota:
            await callback.answer(
                f"Вы исчерпали лимит неиспользованных инвайтов ({user.invite_quota})",
                show_alert=True
            )
            return
        
        invite = await crud.create_invite(db, user.id, None)
        await callback.message.answer(
            f"✅ <b>Создан инвайт-код:</b>\n\n"
            f"<code>{invite.code}</code>",
            parse_mode="HTML"
        )
    await callback.answer()


# ========== ЗАПУСК ==========

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
