from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню с эмодзи"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Баланс", callback_data="balance")
    kb.button(text="⭐️ Пополнить", callback_data="topup")
    kb.button(text="📡 NuxTunnel", callback_data="proxy")
    kb.button(text="🔐 NuxGuard", callback_data="wg_list")
    # kb.button(text="➕ Создать", callback_data="wg_create")
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