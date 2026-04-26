from aiogram import Router
from aiogram.types import CallbackQuery

from services.bot.keyboards import get_back_kb
from services.bot.utils.db_helpers import get_db_session, get_user_by_telegram_id
from db import crud

router = Router()

@router.callback_query(lambda c: c.data == "invites")
async def list_invites(callback: CallbackQuery):
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

@router.callback_query(lambda c: c.data == "create_invite")
async def create_invite_cmd(callback: CallbackQuery):
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
            f"✅ <b>Создан инвайт-код:</b>\n\n<code>{invite.code}</code>",
            parse_mode="HTML"
        )
    await callback.answer()