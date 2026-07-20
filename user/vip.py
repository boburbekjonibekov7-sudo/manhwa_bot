# user/vip.py
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    get_user, get_vip_cards, create_vip_order, update_order,
    get_order, get_user_orders, use_promo, set_vip, get_active_promo,
    get_setting, is_admin
)
from keyboards.user_kb import (
    vip_menu_kb, select_card_kb, select_card_pending_kb,
    payment_confirm_kb, payment_confirm_pending_kb,
    cancel_only_kb, my_orders_empty_kb, back_kb
)
from config import config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = Router()

class VipStates(StatesGroup):
    waiting_receipt = State()
    waiting_promo = State()

# ==================== VIP MENYU ====================
@router.message(F.text.contains("VIP obuna"))
async def cmd_vip(message: Message):
    await show_vip_menu(message, message.from_user.id)

@router.callback_query(F.data == "vip_menu")
async def cb_vip_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_vip_menu(call.message, call.from_user.id, edit=True)

async def show_vip_menu(message, user_id: int, edit=False):
    user = await get_user(user_id)
    price_1w = await get_setting("vip_1week_price") or "4000"
    price_2w = await get_setting("vip_2week_price") or "8000"
    price_1m = await get_setting("vip_1month_price") or "12000"
    
    vip_status = ""
    if user and user.get("is_vip"):
        vip_until = user.get("vip_until", "")
        try:
            until = datetime.fromisoformat(vip_until).strftime("%d.%m.%Y")
            vip_status = f"\n\n👑 Sizning VIP: {until} gacha"
        except:
            pass
    
    text = (
        f"💎 VIP OBUNA{vip_status}\n\n"
        f"VIP obuna orqali siz hech qanday kanallarga obuna bo'lmasdan,\n"
        f"botdan to'liq va cheklovsiz foydalanasiz.\n\n"
        f"┌─────────────────────\n"
        f"│ 💰 NARXLAR          │\n"
        f"├─────────────────────\n"
        f"│ ⏰ 1 hafta  = {int(price_1w):,} so'm │\n"
        f"│ ⏰ 2 hafta = {int(price_2w):,} so'm │\n"
        f"│ ⏰ 1 oy    = {int(price_1m):,} so'm │\n"
        f"└─────────────────────\n\n"
        f"👇 Kerakli muddatni tanlang:"
    )
    
    p1w = int(price_1w)
    p2w = int(price_2w)
    p1m = int(price_1m)
    if edit:
        try:
            await message.edit_text(text, reply_markup=vip_menu_kb(p1w, p2w, p1m))
        except:
            await message.answer(text, reply_markup=vip_menu_kb(p1w, p2w, p1m))
    else:
        await message.answer(text, reply_markup=vip_menu_kb(p1w, p2w, p1m))

# ==================== VIP SOTIB OLISH ====================
@router.callback_query(F.data.startswith("vip_buy:"))
async def cb_vip_buy(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    days = int(parts[1])
    amount = int(parts[2])
    
    cards = await get_vip_cards()
    if not cards:
        await call.answer("❌ Hozircha to'lov kartalari mavjud emas. Admin bilan bog'laning.", show_alert=True)
        return
    
    # VIP buyurtmani darhol yozmaymiz — "To'lov qildim" bosilganda yoziladi
    duration_text = {7: "7 kun", 14: "14 kun", 30: "1 oy"}.get(days, f"{days} kun")
    
    await state.update_data(vip_days=days, vip_amount=amount)
    
    text = (
        f"💳 TO'LOV KARTASINI TANLANG\n\n"
        f"──────────────────\n"
        f"📦 Mahsulot: VIP obuna\n"
        f"⏰ Muddat: {duration_text}\n"
        f"💰 Summa: {amount:,} so'm\n"
        f"──────────────────\n\n"
        f"👇 Quyidagi kartalardan biriga pul o'tkazing:"
    )
    
    await call.message.edit_text(text, reply_markup=select_card_pending_kb(cards, days, amount))

@router.callback_query(F.data.startswith("select_card_pending:"))
async def cb_select_card_pending(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    card_id = int(parts[1])
    
    cards = await get_vip_cards()
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        await call.answer("❌ Karta topilmadi!", show_alert=True)
        return
    
    # Hali buyurtma yaratilmagan — state dan ma'lumot olamiz
    data = await state.get_data()
    days = data.get("vip_days", 0)
    amount = data.get("vip_amount", 0)
    
    duration_text = {7: "7 kun", 14: "14 kun", 30: "1 oy"}.get(days, f"{days} kun")
    
    text = (
        f"💳 KARTA MA'LUMOTLARI\n\n"
        f"──────────────────\n"
        f"💳 TO'LOV KARTASI\n"
        f"──────────────────\n"
        f"Karta👉 {card['card_number']}\n\n"
        f"💰 Summa: {amount:,} so'm\n"
        f"⏰ Muddat: {duration_text}\n"
        f"──────────────────\n\n"
        f"✅ Pul o'tkazmasini amalga oshirgandan so'ng,\n"
        f"«To'lov qildim» tugmasini bosing va chek rasmini yuboring.\n\n"
        f"📌 Eslatma: To'lov chekini yubormasangiz, to'lovingiz tasdiqlanmaydi!"
    )
    
    await state.update_data(vip_card_id=card_id)
    await call.message.edit_text(
        text,
        reply_markup=payment_confirm_pending_kb(),
        parse_mode=None
    )

@router.callback_query(F.data == "payment_done_pending")
async def cb_payment_done_pending(call: CallbackQuery, state: FSMContext):
    """'To'lov qildim' bosilganda vip_order yaratish va chek so'rash."""
    data = await state.get_data()
    days = data.get("vip_days", 0)
    amount = data.get("vip_amount", 0)
    card_id = data.get("vip_card_id")
    
    if not days or not amount:
        await call.answer("❌ Ma'lumot topilmadi! Qaytadan urinib ko'ring.", show_alert=True)
        return
    
    # VIP buyurtmani shu yerda yaratamiz
    order_id = await create_vip_order(call.from_user.id, days, amount)
    
    await state.update_data(order_id=order_id)
    await state.set_state(VipStates.waiting_receipt)
    
    duration_text = {7: "7 kun", 14: "14 kun", 30: "1 oy"}.get(days, f"{days} kun")
    
    await call.message.edit_text(
        f"📸 CHEK YUBORISH\n\n"
        f"🆔 Zakaz: #{order_id}\n"
        f"⏰ Muddat: {duration_text}\n"
        f"💰 Summa: {amount:,} so'm\n\n"
        f"Iltimos, to'lov chekining aniq rasmini yuboring.\n\n"
        f"📌 Talablar:\n"
        f"• Rasm aniq ko'rinishi kerak\n"
        f"• To'lov summasi ko'rinishi kerak\n"
        f"• To'lov vaqti ko'rinishi kerak\n\n"
        f"Admin 5-10 daqiqa ichida tasdiqlaydi.",
        reply_markup=cancel_only_kb(),
        parse_mode=None
    )
    
    # Agar card_id tanlangan bo'lsa, update qilamiz
    if card_id:
        await update_order(order_id, card_id=card_id)


@router.callback_query(F.data.startswith("payment_done:"))
async def cb_payment_done(call: CallbackQuery, state: FSMContext):
    """Eski usul (agar buyurtma allaqachon yaratilgan bo'lsa)."""
    order_id = call.data.split(":")[1]
    
    await state.update_data(order_id=order_id)
    await state.set_state(VipStates.waiting_receipt)
    
    order = await get_order(order_id)
    if not order:
        await call.answer("❌ Zakaz topilmadi!", show_alert=True)
        return
    
    duration_text = {7: "7 kun", 14: "14 kun", 30: "1 oy"}.get(order["duration_days"], f"{order['duration_days']} kun")
    
    await call.message.edit_text(
        f"📸 CHEK YUBORISH\n\n"
        f"🆔 Zakaz: #{order_id}\n"
        f"⏰ Muddat: {duration_text}\n"
        f"💰 Summa: {order['amount']:,} so'm\n\n"
        f"Iltimos, to'lov chekining aniq rasmini yuboring.\n\n"
        f"📌 Talablar:\n"
        f"• Rasm aniq ko'rinishi kerak\n"
        f"• To'lov summasi ko'rinishi kerak\n"
        f"• To'lov vaqti ko'rinishi kerak\n\n"
        f"Admin 5-10 daqiqa ichida tasdiqlaydi.",
        reply_markup=cancel_only_kb(),
        parse_mode=None
    )

@router.message(VipStates.waiting_receipt)
async def process_receipt_any(message: Message, state: FSMContext, bot: Bot):
    if not message.photo:
        await message.answer(
            "❌ Faqat rasm (screenshot) yuboring!\n\nTo'lov chekining rasmini yuboring.",
            reply_markup=cancel_only_kb()
        )
        return
    await _process_receipt_photo(message, state, bot)

async def _process_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data.get("order_id")
    
    if not order_id:
        await state.clear()
        return
    
    receipt_file_id = message.photo[-1].file_id
    await update_order(order_id, receipt_file_id=receipt_file_id, status="waiting")
    await state.clear()
    
    order = await get_order(order_id)
    duration_text = {7: "7 kun", 14: "14 kun", 30: "1 oy"}.get(order["duration_days"], f"{order['duration_days']} kun")
    
    # Foydalanuvchiga xabar
    await message.answer(
        f"✅ Chek qabul qilindi!\n\n"
        f"🆔 Zakaz: #{order_id}\n"
        f"⏰ Muddat: {duration_text}\n"
        f"💰 Summa: {order['amount']:,} so'm\n\n"
        f"Admin 5-10 daqiqa ichida tekshiradi va VIP faollashadi.",
        parse_mode=None
    )
    
    # Adminlarga xabar
    from database.db import get_admins
    admins = await get_admins()
    admin_ids = config.ADMIN_IDS + [a["user_id"] for a in admins]
    
    user = await get_user(message.from_user.id)
    import html as html_lib
    safe_name = html_lib.escape(message.from_user.full_name or "Foydalanuvchi")
    username = message.from_user.username
    if username:
        user_mention = f'<a href="https://t.me/{username}">{safe_name}</a>'
    else:
        user_mention = f'<a href="tg://user?id={message.from_user.id}">{safe_name}</a>'
    
    admin_text = (
        f"💰 Yangi to'lov so'rovi!\n\n"
        f"👤 Foydalanuvchi: {user_mention}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📦 Zakaz: #{order_id}\n"
        f"⏰ Muddat: {duration_text}\n"
        f"💰 Summa: {order['amount']:,} so'm"
    )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"approve_order:{order_id}")
    builder.button(text="❌ Rad etish", callback_data=f"reject_order:{order_id}")
    builder.adjust(2)
    
    for admin_id in set(admin_ids):
        try:
            await bot.send_photo(
                admin_id,
                photo=receipt_file_id,
                caption=admin_text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except:
            pass

# ==================== MENING XARIDLARIM ====================
@router.callback_query(F.data == "my_orders")
async def cb_my_orders(call: CallbackQuery):
    orders = await get_user_orders(call.from_user.id)
    
    if not orders:
        await call.message.edit_text(
            "📋 SIZNING XARIDLARINGIZ\n\n"
            "Siz hali hech qanday xarid qilmagansiz.",
            reply_markup=my_orders_empty_kb(),
            parse_mode=None
        )
        return
    
    text = "📋 SIZNING XARIDLARINGIZ\n\n"
    for o in orders[:10]:
        status_emoji = {"pending": "⏳", "waiting": "🔄", "approved": "✅", "rejected": "❌"}.get(o["status"], "❓")
        duration_text = {7: "1 hafta", 14: "2 hafta", 30: "1 oy"}.get(o["duration_days"], f"{o['duration_days']} kun")
        text += (
            f"{status_emoji} #{o['order_id']} — {duration_text} — {o['amount']:,} so'm\n"
            f"   📅 {o['created_at'][:10]}\n\n"
        )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data="vip_menu")
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode=None)

# ==================== PROMOKOD ====================
@router.callback_query(F.data == "vip_promo")
async def cb_vip_promo(call: CallbackQuery, state: FSMContext):
    promo = await get_active_promo()
    if not promo:
        await call.answer("❌ Hozircha aktiv promokod mavjud emas!", show_alert=True)
        return
    
    await state.set_state(VipStates.waiting_promo)
    await call.message.edit_text(
        "🎟 PROMOKOD\n\n"
        "6 xonali promokodni kiriting:\n\n"
        "Promokod orqali 1 haftalik VIP ishlatasiz!",
        reply_markup=back_kb("vip_menu"),
        parse_mode=None
    )

@router.message(VipStates.waiting_promo)
async def process_promo(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    
    result = await use_promo(code, message.from_user.id)
    
    if not result:
        await message.answer(
            "❌ Promokod noto'g'ri yoki muddati tugagan!",
            reply_markup=back_kb("vip_menu")
        )
        return
    
    if isinstance(result, dict) and result.get("error") == "already_used":
        await message.answer(
            "❌ Siz bu promokodni allaqachon ishlatgansiz!",
            reply_markup=back_kb("vip_menu")
        )
        return
    
    days = result.get("duration_days", 7)
    new_until = await set_vip(message.from_user.id, days)
    await state.clear()
    await message.answer(
        f"✅ Promokod muvaffaqiyatli ishlatildi!\n\n"
        f"💎 VIP faollashdi: {days} kun\n"
        f"📅 Tugash sanasi: {new_until.strftime('%d.%m.%Y')}\n\n"
        f"Endi barcha VIP kontentdan foydalana olasiz!",
        reply_markup=back_kb("main_menu", "🏠 Asosiy menyu"),
        parse_mode=None
    )
