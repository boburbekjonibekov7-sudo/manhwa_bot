# user/anime.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    get_anime, get_anime_by_name, get_all_animes,
    get_episodes, get_seasons, get_user, mark_watched,
    get_watched, increment_search, get_channels, get_setting
)
from keyboards.user_kb import (
    search_type_kb, back_kb, all_animes_kb, anime_info_kb,
    episodes_kb, vip_required_kb, cancel_only_kb
)
from config import config
import logging

logger = logging.getLogger(__name__)
router = Router()

async def send_episode_file(message_or_call_message, ep: dict, caption: str, reply_markup=None, protect_content=False):
    """
    Bob videomi yoki PDF ekaniga qarab to'g'ri metod bilan yuboradi.
    `message_or_call_message` — Message obyekti (call.message yoki message).
    """
    file_type = ep.get("file_type") or "video"
    if file_type == "pdf":
        return await message_or_call_message.answer_document(
            document=ep["file_id"],
            caption=caption,
            reply_markup=reply_markup,
            protect_content=protect_content,
            parse_mode=None
        )
    else:
        return await message_or_call_message.answer_video(
            video=ep["file_id"],
            caption=caption,
            reply_markup=reply_markup,
            protect_content=protect_content,
            parse_mode=None
        )

class SearchStates(StatesGroup):
    waiting_name = State()
    waiting_code = State()

# ==================== ANIME IZLASH MENYU ====================
@router.message(F.text.contains("Manhwa izlash"))
async def cmd_search(message: Message):
    await message.answer(
        "🔍 Qidiruv turini tanlang:",
        reply_markup=search_type_kb()
    )

@router.callback_query(F.data == "search_menu")
async def cb_search_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "🔍 Qidiruv turini tanlang:",
        reply_markup=search_type_kb()
    )

# ==================== NOMI ORQALI ====================
@router.callback_query(F.data == "search_by_name")
async def cb_search_by_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_name)
    await call.message.edit_text(
        "🔍 Manhwa nomini yuboring:",
        reply_markup=back_kb("search_menu")
    )

@router.message(SearchStates.waiting_name)
async def process_name_search(message: Message, state: FSMContext):
    name = message.text.strip()
    results = await get_anime_by_name(name)
    
    if not results:
        await message.answer(
            f"❌ '{name}' nomi bilan manhwa topilmadi.",
            reply_markup=back_kb("search_menu")
        )
        return
    
    if len(results) == 1:
        await state.clear()
        await increment_search(results[0]["code"])
        await show_anime_info(message, results[0]["code"], message.from_user.id)
        return
    
    text = f"🔍 '{name}' bo'yicha {len(results)} ta natija:\n\n"
    for a in results[:10]:
        text += f"🎬 {a['name']} | Kod: {a['code']}\n"
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for a in results[:10]:
        builder.button(text=f"🎬 {a['name']}", callback_data=f"anime_info:{a['code']}")
    builder.button(text="🔙 Orqaga", callback_data="search_menu")
    builder.adjust(1)
    
    await state.clear()
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode=None)

# ==================== KOD ORQALI ====================
@router.callback_query(F.data == "search_by_code")
async def cb_search_by_code(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_code)
    await call.message.edit_text(
        "📌 Manhwa kodini kiriting:\n\nMasalan: 574",
        reply_markup=back_kb("search_menu"),
        parse_mode=None
    )

@router.message(SearchStates.waiting_code)
async def process_code_search(message: Message, state: FSMContext):
    try:
        code = int(message.text.strip())
    except:
        await message.answer(
            "❌ Noto'g'ri kod. Faqat raqam kiriting.",
            reply_markup=back_kb("search_menu")
        )
        return
    
    anime = await get_anime(code)
    if not anime:
        await message.answer(
            f"❌ {code} kodli manhwa topilmadi.",
            reply_markup=back_kb("search_menu")
        )
        return
    
    await state.clear()
    await increment_search(code)
    await show_anime_info(message, code, message.from_user.id)

# ==================== BARCHA ANIMELAR ====================
@router.callback_query(F.data.startswith("search_all:"))
async def cb_all_animes(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    result = await get_all_animes(page=page)
    
    if not result["items"]:
        await call.answer("❌ Hozircha manhwa yo'q!", show_alert=True)
        return
    
    lines = []
    for a in result["items"]:
        eps = await get_episodes(a["code"])
        vip_mark = "💎" if a.get("is_vip") else "🎬"
        lines.append(
            f"{vip_mark} {a['name']}\n"
            f"   🔍 Kod: {a['code']} | 📽 {len(eps)} bob"
        )
    
    text = (
        f"📚 Barcha manhwalar ({result['total']} ta) "
        f"— {page}/{result['pages']} sahifa:\n\n"
        + "\n\n".join(lines)
        + "\n\nKo'rmoqchi bo'lgan manhwani tanlang:"
    )
    
    bot_username = await get_setting("bot_username") or ""
    await call.message.edit_text(
        text,
        reply_markup=all_animes_kb(result["items"], page, result["pages"], bot_username),
        parse_mode=None
    )

# ==================== ANIME INFO ====================
@router.callback_query(F.data.startswith("anime_info:"))
async def cb_anime_info(call: CallbackQuery):
    code = int(call.data.split(":")[1])
    await increment_search(code)
    await show_anime_info(call.message, code, call.from_user.id, edit=True)

async def show_anime_info(message, code: int, user_id: int, edit=False):
    anime = await get_anime(code)
    if not anime:
        if edit:
            await message.edit_text("❌ Manhwa topilmadi.", reply_markup=back_kb("search_menu"))
        else:
            await message.answer("❌ Manhwa topilmadi.", reply_markup=back_kb("search_menu"))
        return
    
    episodes = await get_episodes(code)
    episode_count = len(episodes)
    bot_username_val = await get_setting('bot_username') or 'anime_bot'
    
    # Asosiy kanal
    channels = await get_channels()
    main_channel = next((ch for ch in channels if ch.get("is_main")), channels[0] if channels else None)
    channel_url = None
    if main_channel:
        ch_username = main_channel.get("channel_username") or ""
        channel_url = main_channel.get("channel_url") or (
            f"https://t.me/{ch_username.lstrip('@')}" if ch_username else None
        )
    
    text = (
        f"——————————————\n"
        f"✨ {anime['name']} ✨\n"
        f"——————————————\n"
        f"📽 Boblar soni : {episode_count}\n"
        f"✏️ Janri : {anime.get('genre') or 'Manhwa'}\n"
        f"☁️ Tili : Ozbek\n"
        f"🔍 Kod : {code}\n"
        f"🌐 Manzil: @{bot_username_val}\n"
        f"🔍 Qidirishlar soni : {anime.get('search_count', 0)}"
    )
    
    kb = anime_info_kb(code, channel_url)
    
    if anime.get("poster_file_id"):
        if edit:
            try:
                await message.delete()
            except:
                pass
        await message.answer_photo(
            photo=anime["poster_file_id"],
            caption=text,
            reply_markup=kb,
            parse_mode=None
        )
    else:
        if edit:
            try:
                await message.edit_text(text, reply_markup=kb, parse_mode=None)
            except:
                await message.answer(text, reply_markup=kb, parse_mode=None)
        else:
            await message.answer(text, reply_markup=kb, parse_mode=None)

# ==================== TOMOSHA QILISH ====================
@router.callback_query(F.data.startswith("watch:"))
async def cb_watch(call: CallbackQuery):
    parts = call.data.split(":")
    anime_code = int(parts[1])
    season_num = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 1
    
    await show_episodes(call, anime_code, season_num, page)

@router.callback_query(F.data.startswith("eps_page:"))
async def cb_eps_page(call: CallbackQuery):
    parts = call.data.split(":")
    anime_code = int(parts[1])
    season_num = int(parts[2])
    page = int(parts[3])
    await show_episodes(call, anime_code, season_num, page, edit=True)

@router.callback_query(F.data.startswith("season:"))
async def cb_season(call: CallbackQuery):
    parts = call.data.split(":")
    anime_code = int(parts[1])
    season_num = int(parts[2])
    # Fasl o'zgarganda yangi faslning 1-qismini yuboramiz
    await show_episodes(call, anime_code, season_num, 1, edit=False)

async def show_episodes(call: CallbackQuery, anime_code: int, season_num: int, page: int, edit=False):
    anime = await get_anime(anime_code)
    if not anime:
        await call.answer("❌ Manhwa topilmadi!", show_alert=True)
        return
    
    user = await get_user(call.from_user.id)
    is_vip_user = user and user.get("is_vip", 0)
    
    episodes = await get_episodes(anime_code, season_num)
    seasons = await get_seasons(anime_code)
    watched = await get_watched(call.from_user.id, anime_code, season_num)
    
    if not episodes:
        await call.answer("❌ Bu faslda boblar yo'q!", show_alert=True)
        return
    
    ep = episodes[0]
    bot_un = await get_setting("bot_username") or "manhwa_bot"
    text = f"🎬 {anime['name']} [{season_num}-fasl]\n🤖 @{bot_un}"
    
    kb = episodes_kb(
        anime_code, episodes, seasons, season_num,
        page, watched, is_vip_user
    )
    
    if edit:
        try:
            await call.message.edit_reply_markup(reply_markup=kb)
        except:
            pass
        return
    
    # 1-bobni yuborish
    sharing = await get_setting("sharing_enabled") or "1"
    protect = sharing == "0"
    await send_episode_file(call.message, ep, text, reply_markup=kb, protect_content=protect)

@router.callback_query(F.data.startswith("watch_ep:"))
async def cb_watch_ep(call: CallbackQuery):
    parts = call.data.split(":")
    anime_code = int(parts[1])
    season_num = int(parts[2])
    ep_num = int(parts[3])
    
    from database.db import get_episode
    ep = await get_episode(anime_code, season_num, ep_num)
    if not ep:
        await call.answer("❌ Bob topilmadi!", show_alert=True)
        return
    
    user = await get_user(call.from_user.id)
    is_vip_user = user and user.get("is_vip", 0)
    
    if ep.get("is_vip") and not is_vip_user:
        await call.message.answer(
            "💎 Bu bob VIP foydalanuvchilar uchun!\n\nVIP obuna oling va barcha kontentdan bahramand bo'ling.",
            reply_markup=vip_required_kb()
        )
        return
    
    anime = await get_anime(anime_code)
    bot_un = await get_setting("bot_username") or "manhwa_bot"
    text = f"🎬 {anime['name']} [{ep_num}-bob]\n🤖 @{bot_un}"
    
    await mark_watched(call.from_user.id, anime_code, ep_num, season_num)
    sharing = await get_setting("sharing_enabled") or "1"
    protect = sharing == "0"
    
    # Ulashish tugmasi
    from aiogram.utils.keyboard import InlineKeyboardBuilder as IKB
    share_kb = IKB()
    if season_num == 1:
        share_url = f"https://t.me/{bot_un}?start={anime_code}={ep_num}"
    else:
        share_url = f"https://t.me/{bot_un}?start={anime_code}=S{season_num}={ep_num}"
    share_kb.button(text="↗️ Ulashish", url=f"https://t.me/share/url?url={share_url}")
    
    await send_episode_file(call.message, ep, text, reply_markup=share_kb.as_markup(), protect_content=protect)
    
    # Keyboard yangilash - ko'rilgan qism belgilansin
    try:
        watched = await get_watched(call.from_user.id, anime_code, season_num)
        user2 = await get_user(call.from_user.id)
        is_vip2 = user2 and user2.get("is_vip", 0)
        episodes = await get_episodes(anime_code, season_num)
        seasons = await get_seasons(anime_code)
        kb = episodes_kb(anime_code, episodes, seasons, season_num, 1, watched, is_vip2)
        await call.message.edit_reply_markup(reply_markup=kb)
    except:
        pass

@router.callback_query(F.data.startswith("vip_required:"))
async def cb_vip_required(call: CallbackQuery):
    await call.message.answer(
        "💎 Bu bob VIP foydalanuvchilar uchun!\n\nVIP obuna oling va barcha kontentdan bahramand bo'ling.",
        reply_markup=vip_required_kb()
    )

@router.callback_query(F.data.startswith("download_all:"))
async def cb_download_all(call: CallbackQuery):
    parts = call.data.split(":")
    anime_code = int(parts[1])
    season_num = int(parts[2])
    
    user = await get_user(call.from_user.id)
    is_vip_user = user and user.get("is_vip", 0)
    
    episodes = await get_episodes(anime_code, season_num)
    anime = await get_anime(anime_code)
    
    import asyncio
    bot_un = await get_setting("bot_username") or "manhwa_bot"
    sharing = await get_setting("sharing_enabled") or "1"
    protect = sharing == "0"
    await call.answer("📥 Yuklash boshlanmoqda...", show_alert=False)
    
    for ep in episodes:
        if ep.get("is_vip") and not is_vip_user:
            await call.message.answer(
                "💎 VIP bobga yetdingiz! Davomini ko'rish uchun VIP oling.",
                reply_markup=vip_required_kb()
            )
            break
        text = f"🎬 {anime['name']} [{ep['episode_number']}-bob]\n🤖 @{bot_un}"
        await send_episode_file(call.message, ep, text, protect_content=protect)
        await mark_watched(call.from_user.id, anime_code, ep["episode_number"], season_num)
        await asyncio.sleep(0.3)
