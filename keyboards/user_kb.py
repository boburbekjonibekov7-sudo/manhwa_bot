# keyboards/user_kb.py
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Dict
from config import config

def main_menu_kb(settings: Dict = None) -> ReplyKeyboardMarkup:
    s = settings or {}
    btn = lambda key, default: s.get(key, default)
    
    kb = ReplyKeyboardBuilder()
    kb.button(text=btn("btn_search", "🔍 Manhwa izlash"))
    kb.button(text=btn("btn_guide", "📚 Qo'llanma"))
    kb.button(text=btn("btn_ads", "💰 Reklama va Homiylik"))
    kb.button(text=btn("btn_stats", "📊 Statistika"))
    kb.button(text=btn("btn_about", "🤖 Bot haqida"))
    kb.button(text=btn("btn_vip", "💎 VIP obuna (cheklovlarsiz)"))
    kb.adjust(1, 2, 1, 1, 1)
    return kb.as_markup(resize_keyboard=True)

def search_type_kb(back_text="🔙 Asosiy menyu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏷 Manhwa nomi orqali", callback_data="search_by_name")
    builder.button(text="📌 Kod orqali", callback_data="search_by_code")
    builder.button(text="📚 Barcha manhwalar", callback_data="search_all:1")
    builder.button(text="🔙 Asosiy menyu", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def back_kb(callback="main_menu", text="🔙 Orqaga") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=callback)
    return builder.as_markup()

def back_cancel_kb(back_cb="main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data=back_cb)
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()

def guide_kb(admin_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    admin_un = (admin_username or "").lstrip("@") or "admin"
    builder.button(text="👨‍💼 Admin bilan bog'lanish", url=f"https://t.me/{admin_un}")
    builder.button(text="🔙 Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def ads_kb(admin_username: str, ads_channel: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    admin_un = (admin_username or "").lstrip("@") or "admin"
    ads_un = (ads_channel or "").lstrip("@") or "ads"
    builder.button(text="👨‍💼 Admin bilan bog'lanish", url=f"https://t.me/{admin_un}")
    builder.button(text="📢 Reklama kanali", url=f"https://t.me/{ads_un}")
    builder.button(text="🔙 Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def stats_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Yangilash", callback_data="refresh_stats")
    builder.button(text="🔙 Asosiy menyu", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def about_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data="main_menu")
    return builder.as_markup()

def vip_menu_kb(price_1w: int = 4000, price_2w: int = 8000, price_1m: int = 12000) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"⏰ 1 hafta - {price_1w:,} so'm", callback_data=f"vip_buy:7:{price_1w}")
    builder.button(text=f"⏰ 2 hafta - {price_2w:,} so'm", callback_data=f"vip_buy:14:{price_2w}")
    builder.button(text=f"⏰ 1 oy - {price_1m:,} so'm", callback_data=f"vip_buy:30:{price_1m}")
    builder.button(text="🎟 PROMOKOD", callback_data="vip_promo")
    builder.button(text="📋 Mening xaridlarim", callback_data="my_orders")
    builder.button(text="🔙 Asosiy menyu", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def select_card_kb(cards: List[Dict], order_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for card in cards:
        text = f"💳 {card['card_number']} - {card['card_type']}"
        builder.button(text=text, callback_data=f"select_card:{order_id}:{card['id']}")
    builder.button(text="🔙 Orqaga", callback_data="vip_menu")
    builder.adjust(1)
    return builder.as_markup()

def select_card_pending_kb(cards: List[Dict], days: int, amount: int) -> InlineKeyboardMarkup:
    """VIP buyurtma hali yaratilmagan — karta tanlash uchun."""
    builder = InlineKeyboardBuilder()
    for card in cards:
        text = f"💳 {card['card_number']} - {card['card_type']}"
        builder.button(text=text, callback_data=f"select_card_pending:{card['id']}")
    builder.button(text="🔙 Orqaga", callback_data="vip_menu")
    builder.adjust(1)
    return builder.as_markup()

def payment_confirm_kb(order_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 To'lov qildim", callback_data=f"payment_done:{order_id}")
    builder.button(text="🔙 Orqaga", callback_data="vip_menu")
    builder.adjust(1)
    return builder.as_markup()

def payment_confirm_pending_kb() -> InlineKeyboardMarkup:
    """'To'lov qildim' tugmasi — buyurtma shu yerda yaratiladi."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 To'lov qildim", callback_data="payment_done_pending")
    builder.button(text="🔙 Orqaga", callback_data="vip_menu")
    builder.adjust(1)
    return builder.as_markup()

def cancel_only_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    return builder.as_markup()

def my_orders_empty_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 VIP sotib olish", callback_data="vip_menu")
    builder.button(text="🔙 Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def subscription_check_kb(channels: List[Dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        ch_username = ch.get("channel_username") or ""
        ch_url = ch.get("channel_url") or (f"https://t.me/{ch_username.lstrip('@')}" if ch_username else "https://t.me")
        ch_name = ch.get("channel_name") or ch_username or "Kanal"
        builder.button(text=f"💠 {ch_name}", url=ch_url)
    builder.button(text="✅ Tekshirish", callback_data="check_sub")
    builder.button(text="💎 VIP obuna (cheklovlarsiz)", callback_data="vip_menu")
    builder.adjust(1)
    return builder.as_markup()

def all_animes_kb(animes: List[Dict], page: int, total_pages: int, bot_username: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for anime in animes:
        if bot_username:
            builder.button(
                text=f"🎬 {anime['name']} [{anime['code']}]",
                url=f"https://t.me/{bot_username}?start={anime['code']}"
            )
        else:
            builder.button(
                text=f"🎬 {anime['name']} [{anime['code']}]",
                callback_data=f"anime_info:{anime['code']}"
            )
    
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"search_all:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"search_all:{page+1}"))
    
    builder.adjust(1)
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="search_menu"))
    return builder.as_markup()

def anime_info_kb(anime_code: int, channel_url: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if channel_url:
        builder.button(text="📺 Kanaldan tomosha qilish", url=channel_url)
    builder.button(text="🎬 Tomosha qilish", callback_data=f"watch:{anime_code}:1:1")
    builder.button(text="🔙 Orqaga", callback_data="search_menu")
    builder.adjust(1)
    return builder.as_markup()

def episodes_kb(
    anime_code: int,
    episodes: List[Dict],
    seasons: List[Dict],
    current_season: int,
    page: int,
    watched: List[int],
    is_vip_user: bool,
    per_page: int = 24
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    start = (page - 1) * per_page
    page_eps = episodes[start:start + per_page]
    total_pages = (len(episodes) + per_page - 1) // per_page
    
    row = []
    for i, ep in enumerate(page_eps):
        ep_num = ep["episode_number"]
        ep_is_vip = ep.get("is_vip", 0)
        
        if ep_is_vip and not is_vip_user:
            text = f"💎 {ep_num}"
            cb = f"vip_required:{anime_code}"
        elif ep_num in watched:
            text = f"✅ {ep_num}"
            cb = f"watch_ep:{anime_code}:{current_season}:{ep_num}"
        else:
            text = str(ep_num)
            cb = f"watch_ep:{anime_code}:{current_season}:{ep_num}"
        
        row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    
    # Pagination
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(text="◀️", callback_data=f"eps_page:{anime_code}:{current_season}:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav.append(InlineKeyboardButton(text="▶️", callback_data=f"eps_page:{anime_code}:{current_season}:{page+1}"))
        builder.row(*nav)
    
    # Seasons
    if len(seasons) > 1:
        season_row = []
        for s in seasons:
            sn = s["season_number"]
            if sn == current_season:
                text = f"✅ {sn}-fasl"
            else:
                text = f"{sn}-fasl 🔘"
            season_row.append(InlineKeyboardButton(text=text, callback_data=f"season:{anime_code}:{sn}"))
        builder.row(*season_row)
    
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data=f"close_eps"))
    builder.row(InlineKeyboardButton(text=f"📥 Yuklash (1-{len(episodes)})", callback_data=f"download_all:{anime_code}:{current_season}"))
    builder.row(InlineKeyboardButton(text="🏠 Menyu", callback_data="main_menu"))
    
    return builder.as_markup()

def vip_required_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 VIP olish", callback_data="vip_menu")
    builder.button(text="🔙 Orqaga", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
