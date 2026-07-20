# keyboards/admin_kb.py
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Dict

def admin_main_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="📡 Kanal boshqaruvi")
    kb.button(text="📋 Kodlar ro'yxati")
    kb.button(text="🎬 Manhwa yuklash")
    kb.button(text="📊 Statistika")
    kb.button(text="👥 Adminlar")
    kb.button(text="✉️ Xabar yuborish")
    kb.button(text="📤 Post qilish")
    kb.button(text="📋 Kodlar paneli")
    kb.button(text="🤖 Bot paneli")
    kb.button(text="📖 Qo'llanma")
    kb.button(text="👤 Foydalanuvchi boshqarish")
    kb.button(text="🔙 User panel")
    kb.adjust(1, 2, 2, 2, 2, 1, 1, 1)
    return kb.as_markup(resize_keyboard=True)

def back_admin_kb(cb="admin_panel") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Admin paneli", callback_data=cb)
    return b.as_markup()

def cancel_admin_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    return b.as_markup()

def back_cancel_admin_kb(back_cb="admin_panel") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Orqaga", callback_data=back_cb)
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    b.adjust(2)
    return b.as_markup()

# ==================== KANAL BOSHQARUVI ====================
def channels_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔐 Majburiy obuna kanallari", callback_data="ch_required")
    b.button(text="📢 Asosiy kanallar (post uchun)", callback_data="ch_main")
    b.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b.adjust(1)
    return b.as_markup()

def required_channels_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Kanal qo'shish", callback_data="ch_add")
    b.button(text="📋 Ro'yxatni ko'rish", callback_data="ch_list")
    b.button(text="🗑 Kanalni o'chirish", callback_data="ch_delete")
    b.button(text="🔙 Kanal boshqaruvi", callback_data="admin_channels")
    b.adjust(1)
    return b.as_markup()

def main_channels_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Asosiy kanal qo'shish", callback_data="main_ch_add")
    b.button(text="📋 Asosiy kanallar ro'yxati", callback_data="main_ch_list")
    b.button(text="🗑 Asosiy kanalni o'chirish", callback_data="main_ch_delete")
    b.button(text="🔙 Kanal boshqaruvi", callback_data="admin_channels")
    b.adjust(1)
    return b.as_markup()

def channel_type_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📢 Ommaviy / Shaxsiy (Kanal · Guruh)", callback_data="ch_type:public")
    b.button(text="🔐 Shaxsiy / So'rovli havola", callback_data="ch_type:private_link")
    b.button(text="🌐 Oddiy havola", callback_data="ch_type:url")
    b.button(text="◀️ Orqaga", callback_data="ch_required")
    b.adjust(1)
    return b.as_markup()

def channel_add_method_kb(back_cb="ch_required") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🆔 ID orqali ulash", callback_data="ch_method:id")
    b.button(text="🔗 Havola orqali ulash", callback_data="ch_method:link")
    b.button(text="📨 Postni ulash orqali", callback_data="ch_method:post")
    b.button(text="◀️ Orqaga", callback_data=back_cb)
    b.adjust(1)
    return b.as_markup()

def channels_list_kb(channels: List[Dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ch in channels:
        b.button(
            text=f"🗑 {ch['channel_name'] or ch['channel_username']}",
            callback_data=f"ch_del_confirm:{ch['id']}"
        )
    b.button(text="🔙 Orqaga", callback_data="admin_channels")
    b.adjust(1)
    return b.as_markup()

# ==================== ANIME YUKLASH ====================
def skip_kb(cb="skip_field") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⏭ O'tkazib yuborish (/skip)", callback_data=cb)
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    b.adjust(1)
    return b.as_markup()

def anime_type_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔴 Oddiy", callback_data="anime_type:normal")
    b.button(text="💎 VIP", callback_data="anime_type:vip")
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    b.adjust(2, 1)
    return b.as_markup()

# ==================== POST QILISH ====================
def post_channels_kb(channels: List[Dict], selected: List[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ch in channels:
        ch_id = str(ch["channel_id"])
        tick = "✅" if ch_id in selected else "☑️"
        b.button(
            text=f"{tick} {ch['channel_username'] or ch['channel_name']}",
            callback_data=f"toggle_ch:{ch_id}"
        )
    b.button(text="✅ Barchasiga jo'natish", callback_data="post_select_all")
    b.button(text=f"🚀 Jo'natish ({len(selected)} ta tanlangan)", callback_data="post_send")
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    b.adjust(1)
    return b.as_markup()

# ==================== XABAR YUBORISH ====================
def broadcast_target_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👤 Bitta foydalanuvchiga", callback_data="bc_target:one")
    b.button(text="👥 Barcha foydalanuvchilarga", callback_data="bc_target:all")
    b.button(text="💎 VIP foydalanuvchilarga", callback_data="bc_target:vip")
    b.button(text="⭐ Oddiy foydalanuvchilarga", callback_data="bc_target:normal")
    b.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b.adjust(1, 2, 1)
    return b.as_markup()

def broadcast_type_kb(target: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✍️ Matn yozish", callback_data=f"bc_type:text:{target}")
    b.button(text="🔗 Post (kodi orqali)", callback_data=f"bc_type:code:{target}")
    b.button(text="📎 Post (link orqali)", callback_data=f"bc_type:link:{target}")
    b.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b.adjust(1)
    return b.as_markup()

# ==================== BOT PANELI ====================
def bot_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🤖 Bot holati", callback_data="bp_status")
    b.button(text="🗄 Bazalar bo'yicha", callback_data="bp_database")
    b.button(text="💎 VIP boshqaruvi", callback_data="bp_vip")
    b.button(text="🎬 Manhwa statusi", callback_data="bp_anime_status")
    b.button(text="⚙️ Sozlamalar", callback_data="bp_settings")
    b.button(text="🖼 Video va Rasm", callback_data="bp_media")
    b.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b.adjust(2, 2, 2, 1)
    return b.as_markup()

def bot_status_kb(is_active: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Botni yoqish", callback_data="bs_on")
    b.button(text="⛔ Botni o'chirish", callback_data="bs_off")
    b.button(text="🚫 User ban qilish", callback_data="bs_ban")
    b.button(text="✅ User ban dan chiqarish", callback_data="bs_unban")
    b.button(text="📋 Banlangan userlar", callback_data="bs_banned_list")
    b.button(text="📜 Loglar boshqaruvi", callback_data="bs_logs")
    b.button(text="🔙 Bot paneli", callback_data="bot_panel")
    b.adjust(2, 2, 1, 1, 1)
    return b.as_markup()

def vip_manage_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ VIP berish", callback_data="vm_give")
    b.button(text="❌ VIP olish", callback_data="vm_take")
    b.button(text="💳 Karta boshqaruvi", callback_data="vm_cards")
    b.button(text="💵 Pul qo'shish", callback_data="vm_add_money")
    b.button(text="💸 Pul olish", callback_data="vm_take_money")
    b.button(text="💰 VIP narxini belgilash", callback_data="vm_prices")
    b.button(text="📋 VIP userlar ro'yxati", callback_data="vm_list")
    b.button(text="🧾 To'lov so'rovlari", callback_data="vm_orders")
    b.button(text="👤 Profillarni ko'rish", callback_data="vm_profiles")
    b.button(text="🎟 Promokod boshqaruvi", callback_data="vm_promo")
    b.button(text="💎 Manhwa VIP sozlash", callback_data="vm_vip_anime")
    b.button(text="🔙 Bot paneli", callback_data="bot_panel")
    b.adjust(2, 2, 2, 2, 1, 1, 1, 1)
    return b.as_markup()

def settings_kb(auto_post: str, auto_code: str, sharing: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    ap = "✅ Yoqiq" if auto_post == "1" else "❌ O'chiq"
    ac = "✅ Yoqiq" if auto_code == "1" else "❌ O'chiq"
    sh = "✅ Yoqiq" if sharing == "1" else "❌ O'chiq"
    b.button(text=f"📢 Auto post: {ap}", callback_data="toggle_auto_post")
    b.button(text=f"🔢 Auto kod: {ac}", callback_data="toggle_auto_code")
    b.button(text=f"🔗 Ulashish: {sh}", callback_data="toggle_sharing")
    b.button(text="✏️ Tugma nomlarini tahrirlash", callback_data="edit_btn_names")
    b.button(text="📝 Kirish matnini tahrirlash", callback_data="edit_start_text")
    b.button(text="🖼 Kirish media tahrirlash", callback_data="edit_start_media")
    b.button(text="🤖 Bot username", callback_data="edit_setting:bot_username")
    b.button(text="👨‍💻 Yaratuvchi username", callback_data="edit_setting:creator_username")
    b.button(text="📢 Kanal username", callback_data="edit_setting:channel_username")
    b.button(text="👨‍💼 Admin username", callback_data="edit_setting:admin_username")
    b.button(text="📣 Reklama kanali", callback_data="edit_setting:ads_channel")
    b.button(text="🔖 Bot versiyasi", callback_data="edit_setting:bot_version")
    b.button(text="📖 Qo'llanma matnini tahrirlash", callback_data="edit_guide_text")
    b.button(text="💬 Reklama matnini tahrirlash", callback_data="edit_ads_text")
    b.button(text="🔙 Bot paneli", callback_data="bot_panel")
    b.adjust(1)
    return b.as_markup()

def vip_promo_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🎟 Promokod yaratish", callback_data="promo_create")
    b.button(text="📋 Joriy promokod", callback_data="promo_current")
    b.button(text="🗑 Promokodni o'chirish", callback_data="promo_delete")
    b.button(text="🔙 VIP boshqaruvi", callback_data="bp_vip")
    b.adjust(1)
    return b.as_markup()

def database_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📥 Baza olish", callback_data="db_export")
    b.button(text="📤 Baza yuklash", callback_data="db_import")
    b.button(text="👥 User qo'shish", callback_data="db_add_users")
    b.button(text="♻️ Botni boshlang'ich holatiga qaytarish", callback_data="db_reset")
    b.button(text="🔙 Bot paneli", callback_data="bot_panel")
    b.adjust(2, 1, 1, 1)
    return b.as_markup()

def db_reset_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Ha, o'chirish", callback_data="db_reset_confirm")
    b.button(text="❌ Bekor qilish", callback_data="bp_database")
    b.adjust(1)
    return b.as_markup()

def db_export_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📦 Full baza olish", callback_data="db_export:full")
    b.button(text="👥 Userlar baza olish", callback_data="db_export:users")
    b.button(text="🎬 Manhwalar baza olish", callback_data="db_export:animes")
    b.button(text="🔙 Bazalar", callback_data="bp_database")
    b.adjust(1)
    return b.as_markup()

def orders_kb(orders: List[Dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders[:10]:
        b.button(
            text=f"#{o['order_id']} - {o.get('full_name', 'User')} - {o['amount']:,} so'm",
            callback_data=f"view_order:{o['order_id']}"
        )
    b.button(text="🔙 VIP boshqaruvi", callback_data="bp_vip")
    b.adjust(1)
    return b.as_markup()

def order_actions_kb(order_id: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Tasdiqlash", callback_data=f"approve_order:{order_id}")
    b.button(text="❌ Rad etish", callback_data=f"reject_order:{order_id}")
    b.button(text="🔙 Orqaga", callback_data="vm_orders")
    b.adjust(2, 1)
    return b.as_markup()

def vip_anime_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔢 Bobdan boshlab VIP", callback_data="vip_anime:from_ep")
    b.button(text="📺 Fasldan boshlab VIP", callback_data="vip_anime:from_season")
    b.button(text="💎 Butun manhwani VIP", callback_data="vip_anime:all")
    b.button(text="♻️ Hammasini oddiy qilish", callback_data="vip_anime:clear")
    b.button(text="🔙 VIP boshqaruvi", callback_data="bp_vip")
    b.adjust(1)
    return b.as_markup()

def ep_post_channels_kb(channels: List[Dict], selected: List[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ch in channels:
        ch_id = str(ch["channel_id"])
        tick = "✅" if ch_id in selected else "☑️"
        b.button(
            text=f"{tick} {ch['channel_username'] or ch['channel_name']}",
            callback_data=f"toggle_ep_ch:{ch_id}"
        )
    b.button(text="✅ Barchasiga jo'natish", callback_data="ep_post_select_all")
    b.button(text=f"🚀 Jo'natish ({len(selected)} ta tanlangan)", callback_data="ep_post_send")
    b.button(text="❌ Bekor qilish", callback_data="admin_cancel")
    b.adjust(1)
    return b.as_markup()

def admin_guide_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📖 Qisqa tushuntirish", callback_data="guide_short")
    b.button(text="📚 To'liq tushuntirish", callback_data="guide_full")
    b.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b.adjust(1)
    return b.as_markup()
