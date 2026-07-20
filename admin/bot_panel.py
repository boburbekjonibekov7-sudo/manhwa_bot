# admin/bot_panel.py
import asyncio
import json
import logging
from datetime import datetime
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    get_setting, set_setting, get_all_settings,
    ban_user, unban_user, get_banned_users,
    get_vip_cards, add_vip_card, delete_vip_card,
    set_vip, remove_vip, get_user, get_users_count, get_animes_count,
    get_pending_orders, get_order, update_order, get_user_orders,
    get_admins, add_admin, remove_admin, is_admin,
    create_promo, get_active_promo, delete_promo,
    export_db, import_users, reset_database
)
from keyboards.admin_kb import (
    bot_panel_kb, bot_status_kb, vip_manage_kb, settings_kb,
    database_kb, db_export_kb, orders_kb, order_actions_kb,
    vip_promo_kb, back_admin_kb, cancel_admin_kb, back_cancel_admin_kb,
    vip_anime_kb
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config
from filters.admin_filter import IsAdminFilter

logger = logging.getLogger(__name__)
router = Router()

class BotPanelStates(StatesGroup):
    # Bot holati
    waiting_ban_id = State()
    waiting_unban_id = State()
    # VIP
    waiting_vip_give_id = State()
    waiting_vip_give_days = State()
    waiting_vip_take_id = State()
    waiting_card_number = State()
    waiting_card_type = State()
    waiting_vip_price_week = State()
    waiting_vip_price_2week = State()
    waiting_vip_price_month = State()
    waiting_promo_code = State()
    waiting_reject_reason = State()
    # Adminlar
    waiting_admin_add_id = State()
    waiting_admin_del_id = State()
    # Sozlamalar
    waiting_start_text = State()
    waiting_start_media = State()
    waiting_btn_name = State()
    waiting_btn_value = State()
    # DB
    waiting_db_import = State()
    waiting_user_ids = State()
    # Foydalanuvchi boshqarish
    waiting_fp_user_id = State()
    # Statistika
    pass

# ==================== BOT PANELI ====================
@router.message(F.text == "🤖 Bot paneli", IsAdminFilter())
async def cmd_bot_panel(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("🤖 Bot paneli:", reply_markup=bot_panel_kb())

@router.callback_query(F.data == "bot_panel")
async def cb_bot_panel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🤖 Bot paneli:", reply_markup=bot_panel_kb())

# ==================== BOT HOLATI ====================
@router.callback_query(F.data == "bp_status")
async def cb_bot_status(call: CallbackQuery):
    active = await get_setting("bot_active")
    status = "✅ Yoqilgan" if active == "1" else "❌ O'chirilgan"
    await call.message.edit_text(
        f"🤖 Bot holati: {status}\n\nKerakli amalni tanlang:",
        reply_markup=bot_status_kb(active == "1")
    )

@router.callback_query(F.data == "bs_on")
async def cb_bot_on(call: CallbackQuery):
    await set_setting("bot_active", "1")
    await call.message.edit_text("✅ Bot yoqildi!", reply_markup=back_admin_kb("bot_panel"))

@router.callback_query(F.data == "bs_off")
async def cb_bot_off(call: CallbackQuery):
    await set_setting("bot_active", "0")
    await call.message.edit_text("⛔ Bot o'chirildi!", reply_markup=back_admin_kb("bot_panel"))

@router.callback_query(F.data == "bs_ban")
async def cb_bs_ban(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_ban_id)
    await call.message.edit_text(
        "🚫 Ban qilinuvchi foydalanuvchi ID sini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_ban_id)
async def process_ban_id(message: Message, state: FSMContext, bot: Bot):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    await ban_user(uid)
    await state.clear()
    try:
        await bot.send_message(uid, "🚫 Siz botdan bloklangansiz.")
    except:
        pass
    await message.answer(f"✅ {uid} ban qilindi!", reply_markup=back_admin_kb("bot_panel"))

@router.callback_query(F.data == "bs_unban")
async def cb_bs_unban(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_unban_id)
    await call.message.edit_text(
        "✅ Ban dan chiqariladigan foydalanuvchi ID sini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_unban_id)
async def process_unban_id(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    await unban_user(uid)
    await state.clear()
    await message.answer(f"✅ {uid} ban dan chiqarildi!", reply_markup=back_admin_kb("bot_panel"))

@router.callback_query(F.data == "bs_banned_list")
async def cb_banned_list(call: CallbackQuery):
    users = await get_banned_users()
    if not users:
        await call.message.edit_text("📋 Banlangan foydalanuvchilar yo'q.", reply_markup=back_admin_kb("bot_panel"))
        return
    text = "🚫 Banlangan foydalanuvchilar:\n\n"
    for u in users[:20]:
        text += f"• {u['full_name'] or 'Nomsiz'} | ID: {u['user_id']}\n"
    await call.message.edit_text(text, reply_markup=back_admin_kb("bot_panel"))

@router.callback_query(F.data == "bs_logs")
async def cb_logs(call: CallbackQuery):
    await call.message.edit_text(
        "📜 Loglar boshqaruvi\n\n_Hozircha log fayllari mavjud emas._",
        reply_markup=back_admin_kb("bot_panel")
    )

# ==================== VIP BOSHQARUVI ====================
@router.callback_query(F.data == "bp_vip")
async def cb_vip_manage(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("💎 VIP boshqaruvi:", reply_markup=vip_manage_kb())

@router.callback_query(F.data == "vm_give")
async def cb_vm_give(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_vip_give_id)
    await call.message.edit_text(
        "➕ VIP beriladigan foydalanuvchi ID sini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_vip_give_id)
async def process_vip_give_id(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    await state.update_data(vip_give_id=uid)
    await state.set_state(BotPanelStates.waiting_vip_give_days)
    b = InlineKeyboardBuilder()
    b.button(text="7 kun", callback_data="vip_give_days:7")
    b.button(text="14 kun", callback_data="vip_give_days:14")
    b.button(text="30 kun", callback_data="vip_give_days:30")
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    b.adjust(3, 1)
    await message.answer("⏰ Necha kun VIP berish?", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("vip_give_days:"))
async def cb_vip_give_days(call: CallbackQuery, state: FSMContext, bot: Bot):
    days = int(call.data.split(":")[1])
    data = await state.get_data()
    uid = data["vip_give_id"]
    until = await set_vip(uid, days)
    await state.clear()
    try:
        await bot.send_message(
            uid,
            f"🎉 Sizga {days} kunlik VIP berildi!\n"
            f"📅 Tugash sanasi: {until.strftime('%d.%m.%Y')}"
        )
    except:
        pass
    await call.message.edit_text(
        f"✅ {uid} ga {days} kunlik VIP berildi!",
        reply_markup=back_admin_kb("bp_vip")
    )

@router.callback_query(F.data == "vm_take")
async def cb_vm_take(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_vip_take_id)
    await call.message.edit_text(
        "❌ VIP olinadigan foydalanuvchi ID sini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_vip_take_id)
async def process_vip_take_id(message: Message, state: FSMContext, bot: Bot):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    await remove_vip(uid)
    await state.clear()
    try:
        await bot.send_message(uid, "❌ Sizning VIP obunangiz bekor qilindi.")
    except:
        pass
    await message.answer(f"✅ {uid} ning VIP olindi!", reply_markup=back_admin_kb("bp_vip"))

# ==================== KARTA BOSHQARUVI ====================
@router.callback_query(F.data == "vm_cards")
async def cb_vm_cards(call: CallbackQuery):
    cards = await get_vip_cards()
    b = InlineKeyboardBuilder()
    b.button(text="➕ Karta qo'shish", callback_data="card_add")
    for c in cards:
        b.button(text=f"🗑 {c['card_number']} - {c['card_type']}", callback_data=f"card_del:{c['id']}")
    b.button(text="🔙 VIP boshqaruvi", callback_data="bp_vip")
    b.adjust(1)
    await call.message.edit_text(
        f"💳 Kartalar ro'yxati ({len(cards)} ta):",
        reply_markup=b.as_markup()
    )

@router.callback_query(F.data == "card_add")
async def cb_card_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_card_number)
    await call.message.edit_text(
        "💳 Karta raqamini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_card_number)
async def process_card_number(message: Message, state: FSMContext):
    await state.update_data(card_number=message.text.strip())
    await state.set_state(BotPanelStates.waiting_card_type)
    b = InlineKeyboardBuilder()
    b.button(text="💳 Humo", callback_data="card_type:Humo")
    b.button(text="💳 Uzcard", callback_data="card_type:Uzcard")
    b.button(text="💳 Visa", callback_data="card_type:Visa")
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    b.adjust(3, 1)
    await message.answer("💳 Karta turini tanlang:", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("card_type:"))
async def cb_card_type(call: CallbackQuery, state: FSMContext):
    card_type = call.data.split(":")[1]
    data = await state.get_data()
    await add_vip_card(data["card_number"], card_type)
    await state.clear()
    await call.message.edit_text(
        f"✅ Karta qo'shildi!\n💳 {data['card_number']} - {card_type}",
        reply_markup=back_admin_kb("vm_cards")
    )

@router.callback_query(F.data.startswith("card_del:"))
async def cb_card_del(call: CallbackQuery):
    card_id = int(call.data.split(":")[1])
    await delete_vip_card(card_id)
    await call.message.edit_text("✅ Karta o'chirildi!", reply_markup=back_admin_kb("vm_cards"))

# ==================== VIP NARXLARI ====================
@router.callback_query(F.data == "vm_prices")
async def cb_vm_prices(call: CallbackQuery, state: FSMContext):
    p1 = await get_setting("vip_1week_price") or "4000"
    p2 = await get_setting("vip_2week_price") or "8000"
    p3 = await get_setting("vip_1month_price") or "12000"
    b = InlineKeyboardBuilder()
    b.button(text="⏰ 1 hafta narxini o'zgartirish", callback_data="set_price:week")
    b.button(text="⏰ 2 hafta narxini o'zgartirish", callback_data="set_price:2week")
    b.button(text="⏰ 1 oy narxini o'zgartirish", callback_data="set_price:month")
    b.button(text="🔙 VIP boshqaruvi", callback_data="bp_vip")
    b.adjust(1)
    await call.message.edit_text(
        f"💰 VIP Narxlari:\n\n"
        f"⏰ 1 hafta: {int(p1):,} so'm\n"
        f"⏰ 2 hafta: {int(p2):,} so'm\n"
        f"⏰ 1 oy: {int(p3):,} so'm",
        reply_markup=b.as_markup()
    )

@router.callback_query(F.data.startswith("set_price:"))
async def cb_set_price(call: CallbackQuery, state: FSMContext):
    period = call.data.split(":")[1]
    await state.update_data(price_period=period)
    period_names = {"week": "1 hafta", "2week": "2 hafta", "month": "1 oy"}
    await state.set_state(BotPanelStates.waiting_vip_price_week)
    await call.message.edit_text(
        f"💰 {period_names.get(period, period)} uchun yangi narxni kiriting (so'mda):",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_vip_price_week)
async def process_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except:
        await message.answer("❌ Faqat raqam kiriting!", reply_markup=cancel_admin_kb())
        return
    data = await state.get_data()
    period = data["price_period"]
    key_map = {"week": "vip_1week_price", "2week": "vip_2week_price", "month": "vip_1month_price"}
    await set_setting(key_map[period], str(price))
    await state.clear()
    await message.answer(f"✅ Narx yangilandi: {price:,} so'm", reply_markup=back_admin_kb("vm_prices"))

# ==================== TO'LOV SO'ROVLARI ====================
@router.callback_query(F.data == "vm_orders")
async def cb_vm_orders(call: CallbackQuery):
    orders = await get_pending_orders()
    if not orders:
        await call.message.edit_text(
            "📋 Kutayotgan to'lov so'rovlari yo'q.",
            reply_markup=back_admin_kb("bp_vip")
        )
        return
    await call.message.edit_text(
        f"🧾 Kutayotgan to'lovlar ({len(orders)} ta):",
        reply_markup=orders_kb(orders)
    )

@router.callback_query(F.data.startswith("view_order:"))
async def cb_view_order(call: CallbackQuery):
    order_id = call.data.split(":")[1]
    order = await get_order(order_id)
    if not order:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    duration_text = {7: "7 kun", 14: "14 kun", 30: "1 oy"}.get(order["duration_days"], f"{order['duration_days']} kun")
    text = (
        f"🧾 Zakaz: #{order_id}\n"
        f"👤 User ID: {order['user_id']}\n"
        f"⏰ Muddat: {duration_text}\n"
        f"💰 Summa: {order['amount']:,} so'm\n"
        f"📅 Sana: {order['created_at'][:16]}\n"
        f"📊 Status: {order['status']}"
    )
    kb = order_actions_kb(order_id)
    if order.get("receipt_file_id"):
        try:
            await call.message.delete()
            await call.message.answer_photo(
                photo=order["receipt_file_id"],
                caption=text,
                reply_markup=kb
            )
            return
        except:
            pass
    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("approve_order:"))
async def cb_approve_order(call: CallbackQuery, bot: Bot):
    order_id = call.data.split(":")[1]
    order = await get_order(order_id)
    if not order:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    await update_order(order_id, status="approved")
    until = await set_vip(order["user_id"], order["duration_days"])
    duration_text = {7: "7 kun", 14: "14 kun", 30: "1 oy"}.get(order["duration_days"], f"{order['duration_days']} kun")
    try:
        await bot.send_message(
            order["user_id"],
            f"✅ To'lovingiz tasdiqlandi!\n\n"
            f"💎 VIP faollashdi: {duration_text}\n"
            f"📅 Tugash sanasi: {until.strftime('%d.%m.%Y')}\n\n"
            f"Barcha VIP kontentdan bahramand bo'ling! 🎬"
        )
    except:
        pass
    try:
        if call.message.photo:
            await call.message.edit_caption(
                caption=f"✅ #{order_id} tasdiqlandi! User: {order['user_id']}"
            )
        else:
            await call.message.edit_text(f"✅ #{order_id} tasdiqlandi!")
    except:
        pass

@router.callback_query(F.data.startswith("reject_order:"))
async def cb_reject_order(call: CallbackQuery, state: FSMContext):
    order_id = call.data.split(":")[1]
    await state.update_data(reject_order_id=order_id)
    await state.set_state(BotPanelStates.waiting_reject_reason)
    await call.message.answer(
        "❌ Rad etish sababini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data["reject_order_id"]
    reason = message.text.strip()
    order = await get_order(order_id)
    await update_order(order_id, status="rejected")
    await state.clear()
    try:
        await bot.send_message(
            order["user_id"],
            f"❌ To'lovingiz rad etildi!\n\n"
            f"📋 Zakaz: #{order_id}\n"
            f"📝 Sabab: {reason}\n\n"
            f"Muammo bo'lsa admin bilan bog'laning."
        )
    except:
        pass
    await message.answer(f"✅ #{order_id} rad etildi!", reply_markup=back_admin_kb("vm_orders"))

# ==================== VIP USERLAR ====================
@router.callback_query(F.data == "vm_list")
async def cb_vm_list(call: CallbackQuery):
    from database.db import get_all_users
    users = await get_all_users(vip_only=True)
    if not users:
        await call.message.edit_text("📋 VIP foydalanuvchilar yo'q.", reply_markup=back_admin_kb("bp_vip"))
        return
    text = f"👑 VIP foydalanuvchilar ({len(users)} ta):\n\n"
    for u in users[:20]:
        vip_until = u.get("vip_until", "")[:10] if u.get("vip_until") else "?"
        text += f"• {u['full_name'] or 'Nomsiz'} | {u['user_id']} | {vip_until}\n"
    await call.message.edit_text(text, reply_markup=back_admin_kb("bp_vip"))

# ==================== PUL QO'SHISH / OLISH ====================
class MoneyStates(StatesGroup):
    waiting_add_user_id = State()
    waiting_add_amount = State()
    waiting_take_user_id = State()
    waiting_take_amount = State()

@router.callback_query(F.data == "vm_add_money")
async def cb_vm_add_money(call: CallbackQuery, state: FSMContext):
    await state.set_state(MoneyStates.waiting_add_user_id)
    await call.message.edit_text(
        "💵 Pul qo'shish\n\nFoydalanuvchi ID sini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(MoneyStates.waiting_add_user_id)
async def process_add_money_id(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    user = await get_user(uid)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi!", reply_markup=cancel_admin_kb())
        return
    await state.update_data(money_user_id=uid)
    await state.set_state(MoneyStates.waiting_add_amount)
    await message.answer(
        f"👤 {user['full_name'] or 'Nomsiz'} | {uid}\n\n💵 Qancha kun VIP qo'shish?",
        reply_markup=cancel_admin_kb()
    )

@router.message(MoneyStates.waiting_add_amount)
async def process_add_money_amount(message: Message, state: FSMContext, bot: Bot):
    try:
        days = int(message.text.strip())
    except:
        await message.answer("❌ Faqat raqam!", reply_markup=cancel_admin_kb())
        return
    data = await state.get_data()
    uid = data["money_user_id"]
    until = await set_vip(uid, days)
    await state.clear()
    try:
        await bot.send_message(uid, f"✅ Hisobingizga {days} kunlik VIP qo'shildi!\n📅 Tugash sanasi: {until.strftime('%d.%m.%Y')}")
    except:
        pass
    await message.answer(
        f"✅ {uid} ga {days} kunlik VIP qo'shildi!\n📅 Tugash: {until.strftime('%d.%m.%Y')}",
        reply_markup=back_admin_kb("bp_vip")
    )

@router.callback_query(F.data == "vm_take_money")
async def cb_vm_take_money(call: CallbackQuery, state: FSMContext):
    await state.set_state(MoneyStates.waiting_take_user_id)
    await call.message.edit_text(
        "💸 VIP kunlarini kamaytirish\n\nFoydalanuvchi ID sini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(MoneyStates.waiting_take_user_id)
async def process_take_money_id(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    user = await get_user(uid)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi!", reply_markup=cancel_admin_kb())
        return
    if not user.get("is_vip"):
        await message.answer("❌ Bu foydalanuvchida VIP yo'q!", reply_markup=cancel_admin_kb())
        return
    vip_until = user.get("vip_until", "")[:10]
    await state.update_data(take_user_id=uid)
    await state.set_state(MoneyStates.waiting_take_amount)
    await message.answer(
        f"👤 {user['full_name'] or 'Nomsiz'} | VIP: {vip_until}\n\n💸 Necha kun kamaytirish?",
        reply_markup=cancel_admin_kb()
    )

@router.message(MoneyStates.waiting_take_amount)
async def process_take_money_amount(message: Message, state: FSMContext, bot: Bot):
    try:
        days = int(message.text.strip())
    except:
        await message.answer("❌ Faqat raqam!", reply_markup=cancel_admin_kb())
        return
    data = await state.get_data()
    uid = data["take_user_id"]
    from datetime import datetime, timedelta
    import aiosqlite
    from database.db import DB_PATH
    user = await get_user(uid)
    vip_until_str = user.get("vip_until", "")
    try:
        vip_until = datetime.fromisoformat(vip_until_str)
        new_until = vip_until - timedelta(days=days)
        now = datetime.now()
        if new_until <= now:
            await remove_vip(uid)
            await state.clear()
            try:
                await bot.send_message(uid, "❌ VIP obunangiz bekor qilindi.")
            except:
                pass
            await message.answer(f"✅ {uid} ning VIP bekor qilindi!", reply_markup=back_admin_kb("bp_vip"))
        else:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET vip_until=? WHERE user_id=?", (new_until.isoformat(), uid))
                await db.commit()
            await state.clear()
            try:
                await bot.send_message(uid, f"ℹ️ VIP muddatingiz {days} kun kamaytirildi.\n📅 Yangi tugash sanasi: {new_until.strftime('%d.%m.%Y')}")
            except:
                pass
            await message.answer(
                f"✅ {uid} ning VIP {days} kun kamaytirildi!\n📅 Yangi tugash: {new_until.strftime('%d.%m.%Y')}",
                reply_markup=back_admin_kb("bp_vip")
            )
    except Exception as e:
        await state.clear()
        await message.answer(f"❌ Xatolik: {e}", reply_markup=back_admin_kb("bp_vip"))

# ==================== PROFILLARNI KO'RISH ====================
@router.callback_query(F.data == "vm_profiles")
async def cb_vm_profiles(call: CallbackQuery):
    from database.db import get_all_users
    users = await get_all_users(vip_only=True)
    if not users:
        await call.message.edit_text("📋 VIP foydalanuvchilar yo'q.", reply_markup=back_admin_kb("bp_vip"))
        return
    b = InlineKeyboardBuilder()
    for u in users[:15]:
        vip_until = u.get("vip_until", "")[:10] if u.get("vip_until") else "?"
        b.button(
            text=f"👤 {u['full_name'] or u['user_id']} | {vip_until}",
            callback_data=f"profile_view:{u['user_id']}"
        )
    b.button(text="🔙 VIP boshqaruvi", callback_data="bp_vip")
    b.adjust(1)
    await call.message.edit_text(f"👤 VIP profillar ({len(users)} ta):", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("profile_view:"))
async def cb_profile_view(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    user = await get_user(uid)
    if not user:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    vip_until = user.get("vip_until", "")[:10] if user.get("vip_until") else "Yoq"
    orders = await get_user_orders(uid)
    approved = [o for o in orders if o["status"] == "approved"]
    vip_mark = "✅" if user.get("is_vip") else "❌"
    ban_mark = "✅" if user.get("is_banned") else "❌"
    text = (
        f"👤 Profil:\n\n"
        f"🆔 ID: {user['user_id']}\n"
        f"👤 Ism: {user['full_name'] or 'Nomsiz'}\n"
        f"📱 Username: {user['username'] or 'Yoq'}\n"
        f"💎 VIP: {vip_mark}\n"
        f"📅 VIP tugaydi: {vip_until}\n"
        f"💰 Jami xaridlar: {len(approved)} ta\n"
        f"📅 Royxatdan: {user['joined_at'][:10]}"
    )
    b = InlineKeyboardBuilder()
    b.button(text="💎 VIP berish", callback_data=f"fp_vip_give:{uid}")
    b.button(text="❌ VIP olish", callback_data=f"fp_vip_take:{uid}")
    b.button(text="🔙 Orqaga", callback_data="vm_profiles")
    b.adjust(2, 1)
    await call.message.edit_text(text, reply_markup=b.as_markup())

# ==================== PROMOKOD ====================
@router.callback_query(F.data == "vm_promo")
async def cb_vm_promo(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🎟 Promokod boshqaruvi:", reply_markup=vip_promo_kb())

@router.callback_query(F.data == "promo_create")
async def cb_promo_create(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_promo_code)
    await call.message.edit_text(
        "🎟 6 xonali promokodni kiriting:\n\nMasalan: ABC123",
        reply_markup=cancel_admin_kb(),
        parse_mode=None
    )

@router.message(BotPanelStates.waiting_promo_code)
async def process_promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    if len(code) != 6:
        await message.answer("❌ Promokod 6 ta belgidan iborat bo'lishi kerak!", reply_markup=cancel_admin_kb())
        return
    await create_promo(code, days=7)
    await state.clear()
    await message.answer(
        f"✅ Promokod yaratildi!\n\n🎟 Kod: {code}\n⏰ Muddat: 7 kun",
        reply_markup=back_admin_kb("vm_promo"),
        parse_mode=None
    )

@router.callback_query(F.data == "promo_current")
async def cb_promo_current(call: CallbackQuery):
    promo = await get_active_promo()
    if not promo:
        await call.message.edit_text(
            "❌ Hozircha aktiv promokod yo'q.",
            reply_markup=back_admin_kb("vm_promo")
        )
        return
    used = json.loads(promo.get("used_by", "[]"))
    await call.message.edit_text(
        f"🎟 Joriy promokod:\n\n"
        f"📌 Kod: {promo['code']}\n"
        f"⏰ Muddat: {promo['duration_days']} kun\n"
        f"📅 Tugaydi: {promo['expires_at'][:10]}\n"
        f"👥 Ishlatganlar: {len(used)} ta",
        reply_markup=back_admin_kb("vm_promo"),
        parse_mode=None
    )

@router.callback_query(F.data == "promo_delete")
async def cb_promo_delete(call: CallbackQuery):
    promo = await get_active_promo()
    if not promo:
        await call.answer("❌ Aktiv promokod yo'q!", show_alert=True)
        return
    await delete_promo(promo["code"])
    await call.message.edit_text("✅ Promokod o'chirildi!", reply_markup=back_admin_kb("vm_promo"))

# ==================== VIP ANIME ====================
# vm_vip_anime handler anime_edit.py da implement qilingan (waiting_vip_anime_select state)

# ==================== QO'LLANMA TAHRIRLASH ====================
class GuideStates(StatesGroup):
    waiting_guide_text = State()
    waiting_ads_text = State()

@router.callback_query(F.data == "edit_guide_text")
async def cb_edit_guide_text(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(GuideStates.waiting_guide_text)
    current = await get_setting("guide_text") or ""
    await call.message.edit_text(
        f"📖 Joriy qo'llanma matni:\n\n{current[:200] if current else 'Boʼsh'}\n\n"
        f"Yangi qo'llanma matnini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(GuideStates.waiting_guide_text)
async def process_guide_text(message: Message, state: FSMContext):
    await set_setting("guide_text", message.text)
    await state.clear()
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="⚙️ Sozlamalarga qaytish", callback_data="bp_settings")
    b.adjust(1)
    await message.answer("✅ Qo'llanma matni yangilandi!", reply_markup=b.as_markup())

@router.callback_query(F.data == "edit_ads_text")
async def cb_edit_ads_text(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(GuideStates.waiting_ads_text)
    current = await get_setting("ads_text") or ""
    await call.message.edit_text(
        f"📣 Joriy reklama matni:\n\n{current[:200] if current else 'Boʼsh'}\n\n"
        f"Yangi reklama matnini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(GuideStates.waiting_ads_text)
async def process_ads_text(message: Message, state: FSMContext):
    await set_setting("ads_text", message.text)
    await state.clear()
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="⚙️ Sozlamalarga qaytish", callback_data="bp_settings")
    b.adjust(1)
    await message.answer("✅ Reklama matni yangilandi!", reply_markup=b.as_markup())

# ==================== SOZLAMALAR ====================
@router.callback_query(F.data == "bp_settings")
async def cb_settings(call: CallbackQuery, state: FSMContext):
    await state.clear()
    auto_post = await get_setting("auto_post") or "1"
    auto_code = await get_setting("auto_code") or "1"
    sharing = await get_setting("sharing_enabled") or "1"
    try:
        await call.message.edit_text(
            "⚙️ Sozlamalar:",
            reply_markup=settings_kb(auto_post, auto_code, sharing)
        )
    except:
        await call.message.answer(
            "⚙️ Sozlamalar:",
            reply_markup=settings_kb(auto_post, auto_code, sharing)
        )

@router.callback_query(F.data == "toggle_auto_post")
async def cb_toggle_auto_post(call: CallbackQuery):
    val = await get_setting("auto_post") or "1"
    new_val = "0" if val == "1" else "1"
    await set_setting("auto_post", new_val)
    auto_code = await get_setting("auto_code") or "1"
    sharing = await get_setting("sharing_enabled") or "1"
    try:
        await call.message.edit_reply_markup(reply_markup=settings_kb(new_val, auto_code, sharing))
    except:
        await call.message.edit_text("⚙️ Sozlamalar:", reply_markup=settings_kb(new_val, auto_code, sharing))
    await call.answer("✅ O'zgartirildi!")

@router.callback_query(F.data == "toggle_auto_code")
async def cb_toggle_auto_code(call: CallbackQuery):
    val = await get_setting("auto_code") or "1"
    new_val = "0" if val == "1" else "1"
    await set_setting("auto_code", new_val)
    auto_post = await get_setting("auto_post") or "1"
    sharing = await get_setting("sharing_enabled") or "1"
    try:
        await call.message.edit_reply_markup(reply_markup=settings_kb(auto_post, new_val, sharing))
    except:
        await call.message.edit_text("⚙️ Sozlamalar:", reply_markup=settings_kb(auto_post, new_val, sharing))
    await call.answer("✅ O'zgartirildi!")

@router.callback_query(F.data == "toggle_sharing")
async def cb_toggle_sharing(call: CallbackQuery):
    val = await get_setting("sharing_enabled") or "1"
    new_val = "0" if val == "1" else "1"
    await set_setting("sharing_enabled", new_val)
    auto_post = await get_setting("auto_post") or "1"
    auto_code = await get_setting("auto_code") or "1"
    try:
        await call.message.edit_reply_markup(reply_markup=settings_kb(auto_post, auto_code, new_val))
    except:
        await call.message.edit_text("⚙️ Sozlamalar:", reply_markup=settings_kb(auto_post, auto_code, new_val))
    await call.answer("✅ O'zgartirildi!")

@router.callback_query(F.data == "edit_start_text")
async def cb_edit_start_text(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(BotPanelStates.waiting_start_text)
    try:
        await call.message.edit_text(
            "📝 Yangi kirish matnini kiriting:",
            reply_markup=cancel_admin_kb()
        )
    except:
        await call.message.answer("📝 Yangi kirish matnini kiriting:", reply_markup=cancel_admin_kb())

@router.message(BotPanelStates.waiting_start_text)
async def process_start_text(message: Message, state: FSMContext):
    await set_setting("start_text", message.text)
    await state.clear()
    auto_post = await get_setting("auto_post") or "1"
    auto_code = await get_setting("auto_code") or "1"
    sharing = await get_setting("sharing_enabled") or "1"
    await message.answer("✅ Kirish matni yangilandi!", reply_markup=settings_kb(auto_post, auto_code, sharing))

@router.callback_query(F.data == "edit_start_media")
async def cb_edit_start_media(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(BotPanelStates.waiting_start_media)
    try:
        await call.message.edit_text(
            "🖼 Yangi kirish rasmi yoki videosini yuboring:\n\n/skip — o'chirish",
            reply_markup=cancel_admin_kb()
        )
    except:
        await call.message.answer("🖼 Yangi kirish rasmi yoki videosini yuboring:", reply_markup=cancel_admin_kb())

@router.message(BotPanelStates.waiting_start_media)
async def process_start_media(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "/skip":
        await set_setting("start_media", "")
        await set_setting("start_media_type", "")
    elif message.photo:
        await set_setting("start_media", message.photo[-1].file_id)
        await set_setting("start_media_type", "photo")
    elif message.video:
        await set_setting("start_media", message.video.file_id)
        await set_setting("start_media_type", "video")
    await state.clear()
    auto_post = await get_setting("auto_post") or "1"
    auto_code = await get_setting("auto_code") or "1"
    sharing = await get_setting("sharing_enabled") or "1"
    await message.answer("✅ Kirish media yangilandi!", reply_markup=settings_kb(auto_post, auto_code, sharing))

@router.callback_query(F.data == "edit_btn_names")
async def cb_edit_btn_names(call: CallbackQuery, state: FSMContext):
    await state.clear()
    b = InlineKeyboardBuilder()
    btns = [
        ("🔍 Manhwa izlash", "btn_search"),
        ("📚 Qo'llanma", "btn_guide"),
        ("💰 Reklama va Homiylik", "btn_ads"),
        ("📊 Statistika", "btn_stats"),
        ("🤖 Bot haqida", "btn_about"),
        ("💎 VIP obuna", "btn_vip"),
    ]
    for name, key in btns:
        b.button(text=f"✏️ {name}", callback_data=f"edit_btn:{key}")
    b.button(text="🔙 Sozlamalar", callback_data="bp_settings")
    b.adjust(1)
    await call.message.edit_text("✏️ Qaysi tugma nomini tahrirlaysiz?", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("edit_btn:"))
async def cb_edit_btn(call: CallbackQuery, state: FSMContext):
    await state.clear()
    key = call.data.split(":")[1]
    await state.update_data(edit_btn_key=key)
    await state.set_state(BotPanelStates.waiting_btn_value)
    current = await get_setting(key) or ""
    await call.message.edit_text(
        f"✏️ Yangi nom kiriting:\n\nJoriy: {current}",
        reply_markup=cancel_admin_kb(),
        parse_mode=None
    )

@router.message(BotPanelStates.waiting_btn_value)
async def process_btn_value(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["edit_btn_key"]
    await set_setting(key, message.text.strip())
    await state.clear()
    auto_post = await get_setting("auto_post") or "1"
    auto_code = await get_setting("auto_code") or "1"
    sharing = await get_setting("sharing_enabled") or "1"
    await message.answer("✅ Tugma nomi yangilandi!", reply_markup=settings_kb(auto_post, auto_code, sharing))

# ==================== BOT INFO SOZLAMALARI ====================
class EditSettingState(StatesGroup):
    waiting_value = State()

@router.callback_query(F.data.startswith("edit_setting:"))
async def cb_edit_setting(call: CallbackQuery, state: FSMContext):
    await state.clear()
    key = call.data.split(":")[1]
    labels = {
        "bot_username": "🤖 Bot username (@ siz, masalan: manhwa_bot)",
        "creator_username": "👨‍💻 Yaratuvchi username (masalan: @username)",
        "channel_username": "📢 Kanal username (masalan: @channel)",
        "admin_username": "👨‍💼 Admin username (masalan: @admin)",
        "ads_channel": "📣 Reklama kanali (masalan: @ads)",
        "bot_version": "🔖 Bot versiyasi (masalan: 3.9)",
    }
    current = await get_setting(key) or ""
    await state.update_data(edit_setting_key=key)
    await state.set_state(EditSettingState.waiting_value)
    await call.message.edit_text(
        f"{labels.get(key, key)}\n\n"
        f"Joriy qiymat: {current}\n\n"
        f"Yangi qiymatni kiriting:",
        reply_markup=cancel_admin_kb(),
        parse_mode=None
    )

@router.message(EditSettingState.waiting_value)
async def process_edit_setting(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["edit_setting_key"]
    value = message.text.strip()
    # bot_username uchun @ ni olib tashlash
    if key == "bot_username":
        value = value.lstrip("@")
    await set_setting(key, value)
    await state.clear()
    labels = {
        "bot_username": "Bot username",
        "creator_username": "Yaratuvchi username",
        "channel_username": "Kanal username",
        "admin_username": "Admin username",
        "ads_channel": "Reklama kanali",
        "bot_version": "Bot versiyasi",
    }
    # Sozlamalar sahifasini yangilash
    auto_post = await get_setting("auto_post") or "1"
    auto_code = await get_setting("auto_code") or "1"
    sharing = await get_setting("sharing_enabled") or "1"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b_back = InlineKeyboardBuilder()
    b_back.button(text="⚙️ Sozlamalarga qaytish", callback_data="bp_settings")
    b_back.button(text="🔙 Bot paneli", callback_data="bot_panel")
    b_back.adjust(1)
    await message.answer(
        f"✅ {labels.get(key, key)} yangilandi:\n{value}",
        reply_markup=b_back.as_markup()
    )

# ==================== DATABASE ====================
@router.callback_query(F.data == "bp_database")
async def cb_database(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🗄 Bazalar bo'yicha:", reply_markup=database_kb())

@router.callback_query(F.data == "db_export")
async def cb_db_export(call: CallbackQuery):
    await call.message.edit_text("📥 Qaysi bazani olmoqchisiz?", reply_markup=db_export_kb())

@router.callback_query(F.data.startswith("db_export:"))
async def cb_db_export_type(call: CallbackQuery, bot: Bot):
    export_type = call.data.split(":")[1]
    await call.answer("📦 Baza tayyorlanmoqda...")

    data = await export_db()
    if export_type == "users":
        out = {"users": data.get("users", [])}
        filename = "users_backup.json"
    elif export_type == "animes":
        out = {"animes": data.get("animes", []), "episodes": data.get("episodes", []), "seasons": data.get("seasons", [])}
        filename = "manhwalar_backup.json"
    else:
        out = data
        filename = "full_backup.json"

    import io
    file_bytes = json.dumps(out, ensure_ascii=False, indent=2).encode("utf-8")
    file_obj = io.BytesIO(file_bytes)
    file_obj.name = filename

    from aiogram.types import BufferedInputFile
    await bot.send_document(
        call.from_user.id,
        document=BufferedInputFile(file_bytes, filename=filename),
        caption=f"📦 {filename} — {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

@router.callback_query(F.data == "db_import")
async def cb_db_import(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_db_import)
    await call.message.edit_text(
        "📤 Baza faylini yuklash\n\n"
        "Menga .json formatidagi backup faylini yuboring.\n"
        "Yoki shunchaki ID lar ro'yxati bo'lsa ham bo'ladi.\n\n"
        "Eslatma: Bu amal eski ma'lumotlarni yangilaydi!",
        reply_markup=cancel_admin_kb(),
        parse_mode=None
    )

@router.message(BotPanelStates.waiting_db_import, F.document)
async def process_db_import(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    if not doc.file_name.endswith(".json"):
        await message.answer("❌ Faqat .json fayl!", reply_markup=cancel_admin_kb())
        return
    file = await bot.get_file(doc.file_id)
    import io, aiohttp
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file.file_path}"
        async with session.get(url) as resp:
            content = await resp.read()

    try:
        data = json.loads(content)
        # Faqat userlarni import qilish
        if "users" in data:
            uids = [u["user_id"] for u in data["users"] if "user_id" in u]
            await import_users(uids)
            await state.clear()
            await message.answer(
                f"✅ {len(uids)} ta user import qilindi!",
                reply_markup=back_admin_kb("bp_database")
            )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}", reply_markup=cancel_admin_kb())

@router.callback_query(F.data == "db_add_users")
async def cb_db_add_users(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotPanelStates.waiting_user_ids)
    await call.message.edit_text(
        "👥 Foydalanuvchi ID larini yuboring.\n\n"
        "Har bir ID ni yangi qatorda yuboring.\n"
        "⚠️ Maksimal 2500 ta ID qo'shishingiz mumkin.\n\n"
        "Misol:\n123456789\n987654321\n555666777",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_user_ids)
async def process_user_ids(message: Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    uids = []
    for line in lines[:2500]:
        try:
            uids.append(int(line.strip()))
        except:
            pass
    await import_users(uids)
    await state.clear()
    await message.answer(
        f"✅ {len(uids)} ta foydalanuvchi qo'shildi!",
        reply_markup=back_admin_kb("bp_database")
    )

# ==================== BOTNI BOSHLANG'ICH HOLATGA QAYTARISH ====================
@router.callback_query(F.data == "db_reset")
async def cb_db_reset(call: CallbackQuery):
    from keyboards.admin_kb import db_reset_confirm_kb
    await call.message.edit_text(
        "⚠️ EHTIYOT BO'LING!\n\n"
        "Botni boshlang'ich holatiga qaytarish barcha ma'lumotlarni o'chiradi:\n"
        "• Barcha foydalanuvchilar\n"
        "• Barcha manhwalar va boblar\n"
        "• Barcha VIP kartalar va buyurtmalar\n"
        "• Barcha promokodlar\n"
        "• Barcha kanallar\n"
        "• Barcha adminlar\n\n"
        "Bot sozlamalari saqlanib qoladi.\n\n"
        "Rostdan ham davom etmoqchimisiz?",
        reply_markup=db_reset_confirm_kb(),
        parse_mode=None
    )

@router.callback_query(F.data == "db_reset_confirm")
async def cb_db_reset_confirm(call: CallbackQuery):
    await call.answer("♻️ Bot boshlang'ich holatiga qaytarilmoqda...")
    await reset_database()
    await call.message.edit_text(
        "✅ Bot muvaffaqiyatli boshlang'ich holatiga qaytarildi!\n\n"
        "Barcha ma'lumotlar o'chirildi. Bot sozlamalari saqlanib qoldi.",
        reply_markup=back_admin_kb("bot_panel"),
        parse_mode=None
    )

# ==================== ADMINLAR ====================
@router.message(F.text == "👥 Adminlar", IsAdminFilter())
async def cmd_admins(message: Message):
    if not await is_admin(message.from_user.id):
        return
    admins = await get_admins()
    b = InlineKeyboardBuilder()
    b.button(text="➕ Admin qo'shish", callback_data="admin_add")
    b.button(text="🗑 Admin o'chirish", callback_data="admin_remove")
    b.button(text="📋 Ro'yxat", callback_data="admin_list")
    b.adjust(2, 1)
    text = f"👥 Adminlar ({len(admins)} ta):"
    await message.answer(text, reply_markup=b.as_markup())

@router.callback_query(F.data == "admin_add")
async def cb_admin_add(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(BotPanelStates.waiting_admin_add_id)
    await call.message.edit_text("➕ Yangi admin User ID sini kiriting:", reply_markup=cancel_admin_kb())

@router.message(BotPanelStates.waiting_admin_add_id)
async def process_admin_add(message: Message, state: FSMContext, bot: Bot):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    try:
        chat = await bot.get_chat(uid)
        username = f"@{chat.username}" if chat.username else None
        full_name = chat.full_name
    except:
        username = None
        full_name = "Noma'lum"
    await add_admin(uid, username, full_name)
    await state.clear()
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b2 = InlineKeyboardBuilder()
    b2.button(text="👥 Adminlar", callback_data="admin_list")
    b2.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b2.adjust(1)
    await message.answer(
        f"✅ Admin qo'shildi!\n👤 {full_name}\n🆔 {uid}",
        reply_markup=b2.as_markup()
    )

@router.callback_query(F.data == "admin_remove")
async def cb_admin_remove(call: CallbackQuery):
    admins = await get_admins()
    if not admins:
        await call.answer("❌ Adminlar yo'q!", show_alert=True)
        return
    b = InlineKeyboardBuilder()
    for a in admins:
        b.button(
            text=f"🗑 {a['full_name'] or a['username'] or a['user_id']}",
            callback_data=f"admin_del_do:{a['user_id']}"
        )
    b.button(text="🔙 Orqaga", callback_data="admin_cancel")
    b.adjust(1)
    await call.message.edit_text("🗑 O'chirish uchun adminni tanlang:", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("admin_del_do:"))
async def cb_admin_del_do(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    await remove_admin(uid)
    await call.message.edit_text(f"✅ {uid} admin ro'yxatdan o'chirildi!", reply_markup=back_admin_kb())

@router.callback_query(F.data == "admin_list")
async def cb_admin_list(call: CallbackQuery):
    admins = await get_admins()
    text = "📋 Adminlar ro'yxati:\n\n"
    for a in admins:
        text += f"• {a['full_name'] or 'Nomsiz'} | {a['username'] or ''} | {a['user_id']}\n"
    if not admins:
        text += "Bo'sh"
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b.adjust(1)
    try:
        await call.message.edit_text(text, reply_markup=b.as_markup())
    except:
        await call.message.answer(text, reply_markup=b.as_markup())

# ==================== STATISTIKA (ADMIN) ====================
@router.message(F.text == "📊 Statistika", IsAdminFilter())
async def cmd_admin_stats(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await show_admin_stats(message)

async def show_admin_stats(message: Message, edit=False):
    from database.db import get_users_count, get_animes_count, get_channels, get_pending_orders
    users = await get_users_count()
    content = await get_animes_count()
    channels = await get_channels()
    orders = await get_pending_orders()
    settings = await get_all_settings()
    now = datetime.now()
    bot_username_val = await get_setting("bot_username") or "manhwa_bot"

    auto_post = "✅" if settings.get("auto_post") == "1" else "❌"
    auto_code = "✅" if settings.get("auto_code") == "1" else "❌"
    bot_active = "✅ Yoqiq" if settings.get("bot_active") == "1" else "❌ O'chiq"

    text = (
        f"📊 Admin Statistika — {now.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"👥 Foydalanuvchilar:\n"
        f"   • Jami: {users['total']} ta\n"
        f"   • Bugun: {users['today']} ta\n"
        f"   • VIP: {users['vip']} ta\n"
        f"   • Banned: {users['banned']} ta\n\n"
        f"🎬 Kontent:\n"
        f"   • Manhwalar: {content['total']} ta\n"
        f"   • Boblar: {content['episodes']} ta\n\n"
        f"📢 Kanallar: {len(channels)} ta\n"
        f"🧾 Kutayotgan to'lovlar: {len(orders)} ta\n\n"
        f"⚙️ Bot holati:\n"
        f"   • Bot: {bot_active}\n"
        f"   • Auto post: {auto_post}\n"
        f"   • Auto kod: {auto_code}\n\n"
        f"🤖 Bot: @{bot_username_val}\n"
        f"📅 Sana: {now.strftime('%d.%m.%Y')}\n"
        f"🕐 Soat: {now.strftime('%H:%M')}"
    )

    b = InlineKeyboardBuilder()
    b.button(text="🔄 Yangilash", callback_data="refresh_admin_stats")

    if edit:
        try:
            await message.edit_text(text, reply_markup=b.as_markup())
        except:
            await message.answer(text, reply_markup=b.as_markup())
    else:
        await message.answer(text, reply_markup=b.as_markup())

@router.callback_query(F.data == "refresh_admin_stats")
async def cb_refresh_admin_stats(call: CallbackQuery):
    try:
        await show_admin_stats(call.message, edit=True)
    except:
        await show_admin_stats(call.message, edit=False)
    await call.answer("✅ Yangilandi!")

# ==================== FOYDALANUVCHI PANELI ====================
@router.message(F.text == "👤 Foydalanuvchi boshqarish", IsAdminFilter())
async def cmd_fp(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(BotPanelStates.waiting_fp_user_id)
    await message.answer(
        "👤 Foydalanuvchi ID sini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(BotPanelStates.waiting_fp_user_id)
async def process_fp_user_id(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    user = await get_user(uid)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi!", reply_markup=cancel_admin_kb())
        return
    await state.clear()
    vip_until = user.get("vip_until", "")[:10] if user.get("vip_until") else "Yoq"
    vip_mark2 = "✅" if user.get("is_vip") else "❌"
    ban_mark2 = "✅" if user.get("is_banned") else "❌"
    joined = user["joined_at"][:10] if user.get("joined_at") else "-"
    last_active = user["last_active"][:10] if user.get("last_active") else "-"
    text = (
        f"👤 Foydalanuvchi profili:\n\n"
        f"🆔 ID: {user['user_id']}\n"
        f"👤 Ism: {user['full_name'] or 'Nomsiz'}\n"
        f"📱 Username: {user['username'] or 'Yoq'}\n"
        f"💎 VIP: {vip_mark2}\n"
        f"📅 VIP tugaydi: {vip_until}\n"
        f"🚫 Ban: {ban_mark2}\n"
        f"📅 Qoshilgan: {joined}\n"
        f"🕐 Songi faollik: {last_active}"
    )
    b = InlineKeyboardBuilder()
    b.button(text="💎 VIP berish", callback_data=f"fp_vip_give:{uid}")
    b.button(text="❌ VIP olish", callback_data=f"fp_vip_take:{uid}")
    b.button(text="🚫 Ban qilish", callback_data=f"fp_ban:{uid}")
    b.button(text="✅ Bandan chiqarish", callback_data=f"fp_unban:{uid}")
    b.button(text="🔙 Orqaga", callback_data="admin_cancel")
    b.adjust(2, 2, 1)
    await message.answer(text, reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("fp_vip_give:"))
async def cb_fp_vip_give(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split(":")[1])
    await state.update_data(vip_give_id=uid)
    b = InlineKeyboardBuilder()
    b.button(text="7 kun", callback_data="vip_give_days:7")
    b.button(text="14 kun", callback_data="vip_give_days:14")
    b.button(text="30 kun", callback_data="vip_give_days:30")
    b.button(text="❌ Bekor", callback_data="admin_cancel")
    b.adjust(3, 1)
    await call.message.edit_text("⏰ Necha kun VIP berish?", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("fp_vip_take:"))
async def cb_fp_vip_take(call: CallbackQuery, bot: Bot):
    uid = int(call.data.split(":")[1])
    await remove_vip(uid)
    try:
        await bot.send_message(uid, "❌ VIP obunangiz bekor qilindi.")
    except:
        pass
    await call.message.edit_text(f"✅ {uid} ning VIP olindi!", reply_markup=back_admin_kb())

@router.callback_query(F.data.startswith("fp_ban:"))
async def cb_fp_ban(call: CallbackQuery, bot: Bot):
    uid = int(call.data.split(":")[1])
    await ban_user(uid)
    try:
        await bot.send_message(uid, "🚫 Siz botdan bloklangansiz.")
    except:
        pass
    await call.message.edit_text(f"✅ {uid} ban qilindi!", reply_markup=back_admin_kb())

@router.callback_query(F.data.startswith("fp_unban:"))
async def cb_fp_unban(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    await unban_user(uid)
    await call.message.edit_text(f"✅ {uid} bandan chiqarildi!", reply_markup=back_admin_kb())
