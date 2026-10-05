from aiogram import Router, types
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated

router = Router()

@router.chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER)
)
async def on_user_join(update: ChatMemberUpdated):
    # Игнорируем ботов (опционально)
    if update.new_chat_member.user.is_bot:
        return
    await update.bot.send_message(
        chat_id=update.chat.id,
        text=f"👋 Добро пожаловать, {update.new_chat_member.user.full_name}!"
    )

@router.chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER)
)
async def on_user_leave(update: ChatMemberUpdated):
    if update.old_chat_member.user.is_bot:
        return
    await update.bot.send_message(
        chat_id=update.chat.id,
        text=f"👋 До свидания, {update.old_chat_member.user.full_name}!"
    )