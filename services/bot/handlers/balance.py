from aiogram import Router
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from db.repositories import (
    UserRepository,
    PaymentRepository,
    ServiceRepository,
    ServiceManager,
    WireGuardRepository,
    ProxyRepository,
    RemnawaveRepository,
)
from db.repositories.server import ServerRepository  # если нужен для отладки
from services.bot.keyboards import get_main_menu_kb
from services.bot.utils.db_helpers import get_db_session
from core.config import WIREGUARD_PRICE_STARS  # цена за месяц

router = Router()
logger = logging.getLogger(__name__)

# ---- Вспомогательные функции клавиатур ----
def get_services_kb(user_id: int):
    """Клавиатура для раздела 'Мои сервисы'"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Обновить список", callback_data="refresh_services")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(1)
    return kb.as_markup()

def get_service_actions_kb(service_id: int, is_active: bool):
    """Клавиатура для управления конкретным сервисом"""
    kb = InlineKeyboardBuilder()
    if is_active:
        kb.button(text="⏳ Продлить на 30 дней", callback_data=f"renew_service_{service_id}")
        kb.button(text="🗑 Удалить", callback_data=f"delete_service_{service_id}")
    else:
        kb.button(text="🔄 Активировать", callback_data=f"activate_service_{service_id}")
    kb.button(text="🔙 Назад к сервисам", callback_data="my_services")
    kb.adjust(1)
    return kb.as_markup()

# ---- Обработчики ----
@router.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: CallbackQuery):
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return

        # Подсчёт активных услуг для отображения
        services = await ServiceRepository.get_by_user(db, user.id)
        active_count = sum(1 for s in services if s.is_active)
        expired_count = len(services) - active_count

        text = (
            f"💰 <b>Ваш баланс</b>\n\n"
            f"⭐️ Звёзды: <b>{user.balance_stars:.1f}</b>\n"
            f"🛡 Активных услуг: {active_count}\n"
            f"⏳ Просрочено: {expired_count}\n\n"
            f"💡 Стоимость NuxGuard: {WIREGUARD_PRICE_STARS} ⭐️/мес\n"
            f"💡 NuxTunnel — бесплатно при NuxGuard"
        )
        kb = InlineKeyboardBuilder()
        kb.button(text="⭐️ Пополнить баланс", callback_data="topup")
        kb.button(text="📋 Мои услуги", callback_data="my_services")
        kb.button(text="🔙 Назад", callback_data="back_to_menu")
        kb.adjust(1)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(lambda c: c.data == "my_services")
async def show_services(callback: CallbackQuery):
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Авторизуйтесь через /start", show_alert=True)
            return

        services = await ServiceRepository.get_by_user(db, user.id)
        if not services:
            text = "У вас пока нет активных услуг. Пополните баланс и создайте новую услугу в главном меню."
            kb = InlineKeyboardBuilder()
            kb.button(text="🔙 Назад", callback_data="back_to_menu")
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
            await callback.answer()
            return

        # Формируем список с кнопками на каждый сервис
        kb = InlineKeyboardBuilder()
        for srv in services:
            status_icon = "✅" if srv.is_active else "⛔️"
            name = srv.name or f"{srv.service_type} #{srv.id}"
            expires = srv.expiration_date.strftime("%d.%m.%Y") if srv.expiration_date else "—"
            kb.button(
                text=f"{status_icon} {name} (до {expires})",
                callback_data=f"service_detail_{srv.id}"
            )
        kb.button(text="🔄 Обновить", callback_data="refresh_services")
        kb.button(text="🔙 Назад", callback_data="back_to_menu")
        kb.adjust(1)
        await callback.message.edit_text(
            "📋 <b>Ваши услуги</b>\n\nВыберите услугу для управления:",
            parse_mode="HTML",
            reply_markup=kb.as_markup()
        )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("service_detail_"))
async def service_detail(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[2])
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        service = await ServiceRepository.get_by_id(db, service_id, user_id=user.id)
        if not service:
            await callback.answer("Услуга не найдена", show_alert=True)
            return

        # Собираем информацию
        type_names = {
            'wireguard': '🔐 NuxGuard (WireGuard)',
            'proxy': '📡 NuxTunnel (Proxy)',
            'remnawave': '📡 Remnawave (подписка)',
        }
        type_display = type_names.get(service.service_type, service.service_type)

        status_text = "Активна" if service.is_active else "Неактивна"
        expires = service.expiration_date.strftime("%d.%m.%Y %H:%M") if service.expiration_date else "—"
        server_info = f"Сервер: {service.server_ip}" if service.server_ip else "Сервер не указан"

        text = (
            f"📌 <b>{service.name}</b>\n"
            f"Тип: {type_display}\n"
            f"Статус: {status_text}\n"
            f"Действует до: {expires}\n"
            f"{server_info}\n"
            f"Ссылка: {service.link or '—'}"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_service_actions_kb(service.id, service.is_active)
        )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("renew_service_"))
async def renew_service(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[2])
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        service = await ServiceRepository.get_by_id(db, service_id, user_id=user.id)
        if not service:
            await callback.answer("Услуга не найдена", show_alert=True)
            return

        # Проверяем баланс
        if user.balance_stars < WIREGUARD_PRICE_STARS:
            await callback.answer(
                f"❌ Недостаточно звёзд. Нужно {WIREGUARD_PRICE_STARS} ⭐️ для продления.",
                show_alert=True
            )
            return

        # Списываем и продлеваем
        from datetime import datetime, timedelta
        user.balance_stars -= WIREGUARD_PRICE_STARS
        service.expiration_date = datetime.now() + timedelta(days=30)
        service.is_active = True
        service.updated_at = datetime.now()
        await db.commit()
        await db.refresh(user)
        await db.refresh(service)

        await callback.message.edit_text(
            f"✅ <b>Услуга продлена!</b>\n\n"
            f"Новая дата окончания: {service.expiration_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Остаток баланса: {user.balance_stars:.1f} ⭐️",
            parse_mode="HTML",
            reply_markup=get_service_actions_kb(service.id, True)
        )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("delete_service_"))
async def delete_service(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[2])
    async with get_db_session() as db:
        user = await UserRepository.get_by_telegram_id(db, callback.from_user.id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        service = await ServiceRepository.get_by_id(db, service_id, user_id=user.id)
        if not service:
            await callback.answer("Услуга не найдена", show_alert=True)
            return

        # Удаляем через ServiceManager (удаляет и внешний ресурс)
        success = await ServiceManager.delete_service_by_params(
            db, user.id, service.name, service.service_type
        )
        if not success:
            await callback.answer("❌ Ошибка удаления услуги", show_alert=True)
            return

        # Возвращаемся к списку услуг
        await callback.message.answer("✅ Услуга удалена.", reply_markup=get_main_menu_kb(user.telegram_id))
        # Перенаправляем на my_services (обновлённый список)
        await show_services(callback)
    await callback.answer()

@router.callback_query(lambda c: c.data == "refresh_services")
async def refresh_services(callback: CallbackQuery):
    await show_services(callback)

@router.callback_query(lambda c: c.data == "tariffs")
async def show_tariffs(callback: CallbackQuery):
    text = (
        f"📋 <b>Тарифы NuxClub</b>\n\n"
        f"🔐 <b>NuxGuard (WireGuard)</b>\n"
        f"• Безлимитный тариф\n"
        f"• Стоимость: {WIREGUARD_PRICE_STARS} ⭐️/мес\n"
        f"• Без ограничений по трафику\n\n"
        f"📡 <b>NuxTunnel (Proxy)</b>\n"
        f"• Бесплатно при наличии NuxGuard\n\n"
        f"📡 <b>Remnawave (подписка)</b>\n"
        f"• Доступна по запросу\n\n"
        f"💡 Оплата продлевает услугу автоматически"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐️ Пополнить баланс", callback_data="topup")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(1)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
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
        user = await UserRepository.get_by_telegram_id(db, message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        try:
            amount = int(payment.invoice_payload.split("_")[1])
        except:
            await message.answer("❌ Ошибка обработки платежа")
            return

        # Создаём запись платежа со статусом pending (но можно сразу success)
        # Рекомендуется сначала создать, потом подтвердить
        payment_record = await PaymentRepository.create(
            db=db,
            user_id=user.id,
            amount_stars=amount,
            telegram_payment_id=payment.telegram_payment_charge_id,
            status="pending",
            description="Пополнение через Telegram Stars"
        )
        # Подтверждаем и зачисляем
        await PaymentRepository.complete(
            db=db,
            payment_id=payment_record.id,
            telegram_payment_id=payment.telegram_payment_charge_id
        )
        # Получаем обновлённый баланс пользователя
        updated_user = await UserRepository.get_by_id(db, user.id)
        new_balance = updated_user.balance_stars if updated_user else 0

        await message.answer(
            f"✅ <b>Оплата успешна!</b>\n\n"
            f"⭐️ Зачислено: <b>{amount}</b> звёзд\n"
            f"💰 Новый баланс: <b>{new_balance:.1f}</b> звёзд",
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(message.from_user.id)
        )