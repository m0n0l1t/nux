from aiogram import Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from db.repositories import UserRepository, ProxyRepository, ServiceRepository, WireGuardRepository
from services.amnezia.wireguard_models import WireGuardConfig
from services.bot.states import CreateWGState
from services.bot.keyboards import get_back_kb, get_main_menu_kb, get_wg_options
from services.bot.utils.db_helpers import get_db_session, logger

router = Router()

@router.callback_query(lambda c: c.data == "wg")
async def show_wg_options(callback: CallbackQuery):
    # await callback.answer(reply_markup=get_wg_options())
    await callback.message.answer('опции NuxGuard', reply_markup=get_wg_options())

@router.callback_query(lambda c: c.data == "proxy")
async def show_proxy(callback: CallbackQuery):
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return
        name = f'{callback.from_user.username}_proxy'
        proxy = await ServiceRepository.get_by_user_name_type(db,  user.id, name, 'proxy')
        if not proxy:
            await ProxyRepository.create(db, user.id, name)
            await show_proxy(callback)
            return
        days_left = 0
        text = (
            f"📡 NuxTunnel\n\n"
            f"📛 Название: {proxy.name}\n"
            f"⏳ Осталось дней: {days_left}\n"
        )
        button = InlineKeyboardButton(text="🚀 Подключить прокси", url=proxy.link)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(lambda c: c.data == "wg_list")
async def list_wg(callback: CallbackQuery):

    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return
        services = await ServiceRepository.get_by_telegram_id(db, callback.from_user.id, 'wireguard')
        if not services:
            await callback.message.answer(
                "У вас нет услуг NuxGuard. Создайте первую через меню.",
                reply_markup=get_wg_options()
            )
            await callback.answer()
            return
        for s in services:
            days_left = 0
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

@router.callback_query(lambda c: c.data.startswith("download_"))
async def download_config(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Авторизуйтесь", show_alert=True)
            return
        svc = await ServiceRepository.get_by_id(db, service_id, user.id)
        if not svc:
            await callback.answer("Услуга не найдена", show_alert=True)
            return
        config = WireGuardConfig.from_link(svc.link).to_config_str()
        file_data = config.encode('utf-8')
        await callback.message.answer_document(
            BufferedInputFile(file_data, filename=f"nuxguard_{callback.from_user.first_name}_{svc.name}.conf")
        )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("delete_wg_"))
async def delete_wg(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[2])
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Авторизуйтесь", show_alert=True)
            return
        svc = await ServiceRepository.get_by_id(db, service_id, user.id)
        if svc:
            await WireGuardRepository.delete(db, svc)
            await callback.answer("✅ Услуга удалена", show_alert=True)
            try:
                await callback.message.delete()
            except:
                pass
        else:
            await callback.answer("Услуга не найдена", show_alert=True)
    await callback.answer()

@router.callback_query(lambda c: c.data == "wg_create")
async def create_wg_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "➕ <b>Создание NuxGuard</b>\n\n"
        "Введите название услуги:\n<i>(например, 'Мой сервер')</i>",
        parse_mode="HTML"
    )
    await state.set_state(CreateWGState.waiting_for_name)
    await callback.answer()

@router.message(CreateWGState.waiting_for_name)
async def create_wg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз.")
        return
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, message.from_user.id)
        if not user:
            await message.answer("Ошибка авторизации. Используйте /start")
            await state.clear()
            return
        try:
            logger.error('create_wg_name')
            service = await WireGuardRepository.create(db, user.id, name)
            await message.answer(
                f"✅ <b>Услуга NuxGuard '{name}' создана!</b>\n\n",
                parse_mode="HTML",
                reply_markup=get_main_menu_kb(message.from_user.id)
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка создания: {str(e)}")
    await state.clear()