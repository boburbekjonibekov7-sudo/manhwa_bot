# admin/guide.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.db import get_all_animes, is_admin
from keyboards.admin_kb import admin_guide_kb, back_admin_kb
from aiogram.utils.keyboard import InlineKeyboardBuilder
from filters.admin_filter import IsAdminFilter

router = Router()

# ==================== QO'LLANMA ====================
@router.message(F.text == "📖 Qo'llanma", IsAdminFilter())
async def cmd_admin_guide(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer(
        "📖 Admin panel qo'llanmasi\n\nQaysi turni ko'rmoqchisiz?",
        reply_markup=admin_guide_kb()
    )

@router.callback_query(F.data == "guide_short")
async def cb_guide_short(call: CallbackQuery):
    text = (
        "📖 *QISQA QO'LLANMA*\n\n"
        "📡 *Kanal boshqaruvi* — Majburiy obuna kanallarni qo'shish/o'chirish\n\n"
        "🎬 *Manhwa yuklash* — Yangi manhwa qo'shish, boblar yuklash\n\n"
        "📋 *Kodlar paneli* — Manhwa tahrirlash, bob qo'shish/o'chirish\n\n"
        "📋 *Kodlar ro'yxati* — Barcha manhwalar ro'yxati\n\n"
        "📤 *Post qilish* — Manhwani kanalga post qilish\n\n"
        "✉️ *Xabar yuborish* — Foydalanuvchilarga xabar yuborish\n\n"
        "👥 *Adminlar* — Admin qo'shish/o'chirish\n\n"
        "🤖 *Bot paneli* — Bot sozlamalari, VIP, baza va boshqalar\n\n"
        "👤 *Foydalanuvchi boshqarish* — User ma'lumotlari va boshqaruv\n\n"
        "📊 *Statistika* — To'liq bot statistikasi"
    )
    b = InlineKeyboardBuilder()
    b.button(text="📚 To'liq qo'llanma", callback_data="guide_full")
    b.button(text="🔙 Orqaga", callback_data="admin_cancel")
    b.adjust(1)
    await call.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "guide_full")
async def cb_guide_full(call: CallbackQuery):
    text = (
        "📚 *TO'LIQ QO'LLANMA*\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "📡 *1. KANAL BOSHQARUVI*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "➕ Kanal qo'shish:\n"
        "  • Ommaviy/Shaxsiy — ID, havola yoki post orqali\n"
        "  • So'rovli havola — invite link orqali\n"
        "  • Oddiy havola — Instagram, sayt havolasi\n"
        "📋 Ro'yxat — mavjud kanallarni ko'rish\n"
        "🗑 O'chirish — kanallarni ro'yxatdan olib tashlash\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "🎬 *2. ANIME YUKLASH*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "1. Kod kiriting (masalan: 574)\n"
        "2. Manhwa nomini kiriting\n"
        "3. Janrni kiriting yoki /skip\n"
        "4. Studiyani kiriting yoki /skip\n"
        "5. Posterni yuboring (rasm/video)\n"
        "6. Boblarni ketma-ket yuboring (video yoki PDF)\n"
        "7. /done yozing — saqlandi!\n"
        "Auto post yoqiq bo'lsa — kanalga avtomatik ketadi.\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "📋 *3. KODLAR PANELI (TAHRIRLASH)*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Kodni kiriting → amallarni tanlang:\n"
        "  ✏️ Postni tahrirlash — nom, janr, poster\n"
        "  🔢 Kodni tahrirlash — yangi kod\n"
        "  ➕ Bob qo'shish — yangi video/PDF yuborish\n"
        "  ➕ Fasl qo'shish — yangi fasl\n"
        "  🗑 Bobni o'chirish — raqamini tanlash\n"
        "  🔄 Bobni almashtirish — yangi video/PDF\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "📤 *4. POST QILISH*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "1. Manhwa kodini kiriting\n"
        "2. Kanallarni tanlang (multi-select)\n"
        "3. 'Jo'natish' tugmasini bosing\n"
        "Har kanal o'z nomi bilan alohida post oladi!\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "💎 *5. VIP BOSHQARUVI*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "  ➕ VIP berish — ID va kun miqdori\n"
        "  ❌ VIP olish — ID kiritish\n"
        "  💳 Karta boshqaruvi — karta qo'shish/o'chirish\n"
        "  💰 Narxlar — 1 hafta, 2 hafta, 1 oy\n"
        "  🧾 To'lov so'rovlari — tasdiqlash/rad etish\n"
        "  🎟 Promokod — 6 xonali kod yaratish\n"
        "  💎 Manhwa VIP — bob yoki fasldan VIP qilish\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "⚙️ *6. SOZLAMALAR*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "  📢 Auto post — manhwa yuklaganda avtomatik post\n"
        "  🔢 Auto kod — avtomatik kod generatsiya\n"
        "  🔗 Ulashish — manhwalarni ulashish\n"
        "  ✏️ Tugma nomlari — asosiy menyu tugmalarini o'zgartirish\n"
        "  📝 Kirish matni — /start xabarini o'zgartirish\n"
        "  🖼 Kirish media — /start rasmi/videosi\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "✉️ *7. XABAR YUBORISH*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Kimga:\n"
        "  • Bitta foydalanuvchi — ID kiriting\n"
        "  • Barcha — barcha active userlarga\n"
        "  • VIP — faqat VIP userlarga\n"
        "  • Oddiy — faqat oddiy userlarga\n"
        "Usullar:\n"
        "  ✍️ Matn — HTML formatlash qo'llab-quvvatlanadi\n"
        "  🔗 Kod orqali — manhwa kodi kiritish\n"
        "  📎 Link orqali — kanal post linkini forward qilish\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "🗄 *8. BAZA BOSHQARUVI*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "  📥 Baza olish — full/userlar/manhwalar JSON\n"
        "  📤 Baza yuklash — JSON fayldan import\n"
        "  👥 User qo'shish — ID ro'yxati (max 2500)\n"
    )

    b = InlineKeyboardBuilder()
    b.button(text="📖 Qisqa ko'rinish", callback_data="guide_short")
    b.button(text="🔙 Orqaga", callback_data="admin_cancel")
    b.adjust(1)
    await call.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="Markdown")

# ==================== KODLAR RO'YXATI (BO'LIMLARGA AJRATISH) ====================
@router.message(F.text == "📋 Kodlar ro'yxati", IsAdminFilter())
async def cmd_codes_list(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await show_codes_sections(message)

async def show_codes_sections(message, edit=False):
    """Bo'limlarga ajratilgan kodlar ro'yxati."""
    from database.db import get_codes_sections
    result = await get_codes_sections()

    total = result["total"]
    normal_count = result["normal_count"]
    ongoing_count = result["ongoing_count"]
    vip_count = result["vip_count"]

    text = (
        f"📋 Kodlar ro'yxati\n"
        f"Jami: {total} ta\n"
        f"Oddiy: {normal_count} ta\n"
        f"Ongoing: {ongoing_count} ta\n"
        f"VIP: {vip_count} ta\n\n"
        f"Bo'limni tanlang:"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    b = InlineKeyboardBuilder()
    for idx, section in enumerate(result["sections"]):
        if section["type"] == "ongoing":
            b.button(
                text=f"{section['label']} {section['range']}",
                callback_data=f"codes_section:{idx}"
            )
        elif section["type"] == "vip":
            b.button(
                text=f"{section['label']} {section['range']}",
                callback_data=f"codes_section:{idx}"
            )
        else:
            b.button(
                text=f"{section['label']} {section['range']}",
                callback_data=f"codes_section:{idx}"
            )

    b.button(text="Hammasini chiqarish", callback_data="codes_all")
    b.button(text="🔙 Admin paneli", callback_data="admin_panel")
    b.adjust(2)

    if edit:
        await message.edit_text(text, reply_markup=b.as_markup(), parse_mode=None)
    else:
        await message.answer(text, reply_markup=b.as_markup(), parse_mode=None)

@router.callback_query(F.data == "codes_all")
async def cb_codes_all(call: CallbackQuery):
    """Hammasini chiqarish tugmasi — barcha manhwalar ro'yxati."""
    from database.db import get_all_active_animes, get_setting, get_episodes
    items = await get_all_active_animes()
    if not items:
        await call.message.edit_text(
            "📋 Kodlar ro'yxati bo'sh.",
            reply_markup=back_admin_kb("admin_panel"),
            parse_mode=None
        )
        return

    bot_username = await get_setting("bot_username") or "manhwa_bot"
    text = f"📋 Barcha manhwalar ({len(items)} ta):\n\n"

    b = InlineKeyboardBuilder()
    for a in items:
        eps = await get_episodes(a["code"])
        vip_mark = "💎" if a.get("is_vip") else "🔴"
        text += f"{vip_mark} [{a['code']}] {a['name']} — {len(eps)} bob\n"

    text += "\nQaysi manhwani tahrirlamoqchisiz?"

    # Har bir manhwa uchun tugma
    for a in items:
        b.button(
            text=f"[{a['code']}] {a['name']}",
            callback_data=f"edit_anime_quick:{a['code']}"
        )

    b.button(text="🔙 Kodlar ro'yxati", callback_data="codes_list_main")
    b.adjust(1)

    await call.message.edit_text(text, reply_markup=b.as_markup(), parse_mode=None)

@router.callback_query(F.data == "codes_list_main")
async def cb_codes_list_main(call: CallbackQuery):
    await show_codes_sections(call.message, edit=True)

@router.callback_query(F.data.startswith("codes_section:"))
async def cb_codes_section(call: CallbackQuery):
    from database.db import get_section_animes, get_setting, get_episodes
    section_index = int(call.data.split(":")[1])
    result = await get_section_animes(section_index)
    items = result.get("items", [])
    section = result.get("section")

    if not items or not section:
        await call.message.edit_text(
            "📋 Bu bo'limda manhwa yo'q.",
            reply_markup=back_admin_kb("codes_list_main"),
            parse_mode=None
        )
        return

    bot_username = await get_setting("bot_username") or "manhwa_bot"
    text = f"📋 {section['label']} {section['range']} ({section['count']} ta):\n\n"

    b = InlineKeyboardBuilder()
    for a in items:
        eps = await get_episodes(a["code"])
        vip_mark = "💎" if a.get("is_vip") else "🔴"
        text += f"{vip_mark} [{a['code']}] {a['name']} — {len(eps)} bob\n"

    text += "\nQaysi manhwani tahrirlamoqchisiz?"

    for a in items:
        b.button(
            text=f"[{a['code']}] {a['name']}",
            callback_data=f"edit_anime_quick:{a['code']}"
        )

    b.button(text="🔙 Kodlar ro'yxati", callback_data="codes_list_main")
    b.adjust(1)

    await call.message.edit_text(text, reply_markup=b.as_markup(), parse_mode=None)

@router.callback_query(F.data.startswith("edit_anime_quick:"))
async def cb_edit_anime_quick(call: CallbackQuery, state: FSMContext):
    code = int(call.data.split(":")[1])
    from database.db import get_anime, get_episodes, get_seasons
    anime = await get_anime(code)
    if not anime:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    eps = await get_episodes(code)
    seasons = await get_seasons(code)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Postni tahrirlash", callback_data=f"edit_post:{code}")
    b.button(text="🔢 Kodni tahrirlash", callback_data=f"edit_code_change:{code}")
    b.button(text="➕ Bob qo'shish", callback_data=f"edit_add_ep:{code}")
    b.button(text="➕ Fasl qo'shish", callback_data=f"edit_add_season:{code}")
    b.button(text="🗑 Bobni o'chirish", callback_data=f"edit_del_ep:{code}")
    b.button(text="🔄 Bobni almashtirish", callback_data=f"edit_replace_ep:{code}")
    b.button(text="🗑 Manhwani o'chirish", callback_data=f"delete_anime_confirm:{code}")
    b.button(text="🔙 Kodlar ro'yxati", callback_data="codes_list_main")
    b.adjust(1)
    await call.message.edit_text(
        f"📋 {anime['name']}\n"
        f"🔢 Kod: {code}\n"
        f"📦 Boblar: {len(eps)} ta | 📺 Fasllar: {len(seasons)} ta\n\n"
        f"Qaysi amalni bajarmoqchisiz?",
        reply_markup=b.as_markup(),
        parse_mode=None
    )
