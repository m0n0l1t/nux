from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import ADMIN_TG

def get_main_menu_kb(tid: int) -> InlineKeyboardMarkup:
    """Главное меню с эмодзи"""
    kb = InlineKeyboardBuilder()

    if str(tid) == ADMIN_TG:
        kb.button(text="💰 Баланс бота", callback_data="balance_bot")

    kb.button(text="💰 Баланс", callback_data="balance")
    kb.button(text="⭐️ Пополнить", callback_data="topup")
    # kb.button(text="📡 NuxTunnel", callback_data="proxy")
    kb.button(text="🔐 NuxGuard", callback_data="wg")
    kb.button(text="📖 Инструкции", callback_data="instructions")
    kb.button(text="🎫 Инвайты", callback_data="invites")
    kb.button(text="✨ Создать инвайт", callback_data="create_invite")
    kb.button(text="📋 Тарифы", callback_data="tariffs")
    kb.adjust(2)
    return kb.as_markup()

def get_back_kb(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    """Кнопка Назад"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data=callback_data)
    return kb.as_markup()

def get_wg_options() -> InlineKeyboardMarkup:
    """Кнопка опций накс гарда"""
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Создать новый конфиг", callback_data="wg_create")
    kb.button(text="🔐 Список существующих", callback_data="wg_list")
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    return kb.as_markup()