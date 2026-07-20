# admin/panel.py
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.db import is_admin, get_all_settings
from keyboards.admin_kb import admin_main_kb, back_admin_kb
from config import config
import logging

logger = logging.getLogger(__name__)
router = Router()

async def admin_check(user_id: int) -> bool:
    return await is_admin(user_id)

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not await admin_check(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    await state.clear()
    await message.answer(
        f"👮 Admin panel:\n\nXush kelibsiz, {message.from_user.first_name}!",
        reply_markup=admin_main_kb()
    )

@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: CallbackQuery, state: FSMContext):
    if not await admin_check(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await state.clear()
    try:
        await call.message.delete()
    except:
        pass
    await call.message.answer("👮 Admin panel:", reply_markup=admin_main_kb())

@router.callback_query(F.data == "admin_cancel")
async def cb_admin_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    from keyboards.admin_kb import back_admin_kb
    try:
        await call.message.edit_text(
            "👮 Admin panel:",
            reply_markup=back_admin_kb()
        )
    except:
        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer("👮 Admin panel:", reply_markup=admin_main_kb())
    await call.answer()

@router.message(F.text == "🔙 User panel")
async def cmd_back_to_user(message: Message, state: FSMContext, bot: Bot):
    if not await admin_check(message.from_user.id):
        return
    await state.clear()
    from user.start import send_start
    await send_start(message, bot, message.from_user.id)
