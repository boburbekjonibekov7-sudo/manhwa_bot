# user/start.py
from aiogram import Bot, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ChatJoinRequest
from aiogram.fsm.context import FSMContext
from database.db import (
    get_user, get_channels, get_setting, get_all_settings,
    get_users_count, get_animes_count, is_admin,
    save_join_request, has_join_request
)
from keyboards.user_kb import (
    main_menu_kb, subscription_check_kb, back_kb, stats_kb, about_kb
)
from config import config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.chat_join_request()
async def handle_join_request(update: ChatJoinRequest):
    """
    Foydalanuvchi shaxsiy/so'rovli kanalga qo'shilish so'rovi yuborganda
    Telegram shu update'ni yuboradi. Admin so'rovni hali tasdiqlamagan
    bo'lsa ham, so'rov yuborilgan bo'lsa YETARLI deb hisoblaymiz.
    """
    try:
        await save_join_request(update.from_user.id, str(update.chat.id))
        logger.info(f"Join request saqlandi: user={update.from_user.id}, chat={update.chat.id}")
    except Exception as e:
        logger.error(f"Join request saqlashda xatolik: {e}")

async def check_subscription(bot, user_id: int) -> bool:
    """
    Majburiy kanallarga obunani tekshirish.
    Avval haqiqiy a'zolik (get_chat_member) tekshiriladi. Agar bu orqali
    a'zo emas deb chiqsa, kanal so'rovli (join request) bo'lishi mumkin —
    bunday holda foydalanuvchi so'rov yuborgan bo'lsa (garchi admin hali
    tasdiqlamagan bo'lsa ham) YETARLI deb hisoblanadi.
    """
    channels = await get_channels()
    sub_channels = [ch for ch in channels if ch["channel_type"] in ["public", "private"]]

    if not sub_channels:
        return True

    for ch in sub_channels:
        is_ok = False
        try:
            member = await bot.get_chat_member(ch["channel_id"], user_id)
            if member.status not in ["left", "kicked", "banned"]:
                is_ok = True
        except:
            pass

        if not is_ok:
            # Oddiy a'zolik topilmadi — so'rov yuborilganmi tekshiramiz
            if await has_join_request(user_id, ch["channel_id"]):
                is_ok = True

        if not is_ok:
            return False

    return True

async def send_start(message: Message, bot: Bot, user_id: int):
    """Start xabarini yuborish"""
    settings = await get_all_settings()
    
    # VIP tekshirish
    user = await get_user(user_id)
    is_vip = user and user.get("is_vip")
    admin = await is_admin(user_id)
    
    # Obuna tekshirish (VIP va admin uchun o'tkazib yuborish)
    if not is_vip and not admin:
        channels = await get_channels()
        # Ko'rsatish uchun: barcha majburiy obuna kanallari (public, private, url)
        display_channels = [ch for ch in channels if not ch.get("is_main")]
        # Tekshirish uchun: faqat bot chat_id orqali a'zolikni bila oladigan turlar
        check_channels = [ch for ch in channels if ch["channel_type"] in ["public", "private"]]

        if display_channels:
            subscribed = await check_subscription(bot, user_id) if check_channels else True
            if not subscribed:
                text = (
                    "⚠️ Botdan to'liq foydalanish uchun quyidagi "
                    "kanallarga obuna bo'ling!\n\n"
                    "──────────────────\n\n"
                    "✅ Yoki VIP obunasini sotib oling\n"
                    "Botdan hech qanday kanallarga obuna bo'lmasdan "
                    "cheklovlarsiz foydalaning!\n"
                    "──────────────────"
                )
                await message.answer(
                    text,
                    reply_markup=subscription_check_kb(display_channels)
                )
                return
    
    start_text = settings.get("start_text", "Manhwa Botiga xush kelibsiz! 🎬")
    start_media = settings.get("start_media", "")
    start_media_type = settings.get("start_media_type", "")
    
    kb = main_menu_kb(settings)
    
    bot_username = settings.get("bot_username", "manhwa_bot")
    status_text = "👑 VIP" if is_vip else "active"
    welcome = (
        f"🤖 {settings.get('btn_about', 'Bot haqida').replace('🤖 ', '')}\n\n"
        f"✨ @{bot_username} Manhwa Botiga xush kelibsiz, "
        f"{message.from_user.first_name or message.from_user.id}!\n\n"
        f"📊 Status: {status_text}\n"
        f"🆔 Sizning ID: {user_id}\n\n"
        f"👇 Quyidagi tugmalar orqali botdan foydalaning:"
    )
    
    if start_media and start_media_type == "photo":
        await message.answer_photo(photo=start_media, caption=welcome, reply_markup=kb, parse_mode=None)
    elif start_media and start_media_type == "video":
        await message.answer_video(video=start_media, caption=welcome, reply_markup=kb, parse_mode=None)
    else:
        await message.answer(welcome, reply_markup=kb, parse_mode=None)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    # Deep link: /start 574 yoki /start 574=3 yoki /start 574=S2=3
    args = message.text.split() if message.text else []
    if len(args) > 1:
        param = args[1].strip()
        try:
            # Parse: KOD=QISM yoki KOD=SSAYL=QISM
            parts = param.split("=")
            code = int(parts[0])
            episode_num = None
            season_num = 1
            
            if len(parts) == 2:
                # KOD=QISM
                episode_num = int(parts[1])
            elif len(parts) == 3 and parts[1].startswith("S"):
                # KOD=S2=QISM
                season_num = int(parts[1][1:])
                episode_num = int(parts[2])
            
            from database.db import get_anime, get_episode
            anime = await get_anime(code)
            if anime:
                user = await get_user(message.from_user.id)
                is_vip_user = user and user.get("is_vip")
                admin = await is_admin(message.from_user.id)
                if not is_vip_user and not admin:
                    subscribed = await check_subscription(bot, message.from_user.id)
                    if not subscribed:
                        # Kodni state ga saqlaymiz - obunadan keyin shu animega yo'naltirish uchun
                        await state.update_data(
                            pending_anime_code=code,
                            pending_episode=episode_num,
                            pending_season=season_num
                        )
                        channels = await get_channels()
                        display_channels = [ch for ch in channels if not ch.get("is_main")]
                        text = (
                            "⚠️ Botdan to'liq foydalanish uchun quyidagi "
                            "kanallarga obuna bo'ling!\n\n"
                            "──────────────────\n\n"
                            "✅ Yoki VIP obunasini sotib oling\n"
                            "──────────────────"
                        )
                        from keyboards.user_kb import subscription_check_kb
                        await message.answer(text, reply_markup=subscription_check_kb(display_channels))
                        return
                
                settings = await get_all_settings()
                kb = main_menu_kb(settings)
                await message.answer(
                    f"✨ Manhwa topildi!",
                    reply_markup=kb
                )
                
                if episode_num is not None:
                    # Aniq qismni yuborish
                    ep = await get_episode(code, season_num, episode_num)
                    if ep:
                        if ep.get("is_vip") and not is_vip_user and not admin:
                            from keyboards.user_kb import vip_required_kb
                            await message.answer(
                                "💎 Bu bob VIP foydalanuvchilar uchun!",
                                reply_markup=vip_required_kb()
                            )
                            return
                        bot_un = await get_setting("bot_username") or "manhwa_bot"
                        sharing = await get_setting("sharing_enabled") or "1"
                        protect = sharing == "0"
                        text_ep = f"🎬 {anime['name']} [{episode_num}-bob]\n🤖 @{bot_un}"
                        from database.db import mark_watched
                        await mark_watched(message.from_user.id, code, episode_num, season_num)
                        from user.anime import send_episode_file
                        await send_episode_file(message, ep, text_ep, protect_content=protect)
                    else:
                        from user.anime import show_anime_info
                        await show_anime_info(message, code, message.from_user.id)
                else:
                    from user.anime import show_anime_info
                    await show_anime_info(message, code, message.from_user.id)
                return
        except (ValueError, TypeError, IndexError):
            pass

    await send_start(message, bot, message.from_user.id)

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    try:
        await call.message.delete()
    except:
        pass
    await send_start(call.message, bot, call.from_user.id)

@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery, bot: Bot, state: FSMContext):
    subscribed = await check_subscription(bot, call.from_user.id)
    if subscribed:
        try:
            await call.message.delete()
        except:
            pass

        # Agar deep link orqali anime kodi saqlangan bo'lsa - o'sha animega yo'naltirish
        data = await state.get_data()
        pending_code = data.get("pending_anime_code")
        pending_episode = data.get("pending_episode")
        pending_season = data.get("pending_season", 1)

        if pending_code:
            # Deep link orqali kelgan - asosiy menyu + o'sha anime
            settings = await get_all_settings()
            kb = main_menu_kb(settings)
            await call.message.answer(
                f"✅ Obuna tasdiqlandi! Xush kelibsiz, {call.from_user.first_name}!",
                reply_markup=kb
            )
            await state.clear()
            from database.db import get_anime, get_episode
            anime = await get_anime(pending_code)
            if anime:
                if pending_episode:
                    ep = await get_episode(pending_code, pending_season, pending_episode)
                    if ep:
                        user = await get_user(call.from_user.id)
                        is_vip_user = user and user.get("is_vip")
                        admin = await is_admin(call.from_user.id)
                        if ep.get("is_vip") and not is_vip_user and not admin:
                            from keyboards.user_kb import vip_required_kb
                            await call.message.answer(
                                "💎 Bu bob VIP foydalanuvchilar uchun!",
                                reply_markup=vip_required_kb()
                            )
                            return
                        bot_un = await get_setting("bot_username") or "manhwa_bot"
                        sharing = await get_setting("sharing_enabled") or "1"
                        protect = sharing == "0"
                        text_ep = f"🎬 {anime['name']} [{pending_episode}-bob]\n🤖 @{bot_un}"
                        from database.db import mark_watched
                        await mark_watched(call.from_user.id, pending_code, pending_episode, pending_season)
                        from user.anime import send_episode_file
                        await send_episode_file(call.message, ep, text_ep, protect_content=protect)
                        return
                from user.anime import show_anime_info
                await show_anime_info(call.message, pending_code, call.from_user.id)
        else:
            # Oddiy /start orqali kelgan - to'liq start xabarini ko'rsatamiz
            await send_start(call.message, bot, call.from_user.id)
    else:
        await call.answer("❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)

@router.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.delete()
    except:
        pass

@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()

@router.callback_query(F.data == "close_eps")
async def cb_close_eps(call: CallbackQuery):
    try:
        await call.message.delete()
    except:
        pass

# ==================== STATISTIKA ====================
@router.message(F.text.contains("Statistika"))
async def cmd_stats(message: Message):
    await show_stats(message)

async def show_stats(message: Message, edit=False):
    users = await get_users_count()
    content = await get_animes_count()
    settings = await get_all_settings()
    now = datetime.now()
    
    text = (
        f"📊 Bot statistikasi:\n\n"
        f"👥 Foydalanuvchilar:\n"
        f"   • Jami: {users['total']} ta\n"
        f"   • Bugun: {users['today']} ta\n\n"
        f"🎬 Kontent:\n"
        f"   • Manhwalar: {content['total']} ta\n"
        f"   • Boblar: {content['episodes']} ta\n\n"
        f"⚙️ Texnik ma'lumotlar:\n"
        f"   • Bot: @{settings.get('bot_username', 'manhwa_bot')}\n"
        f"   • Yuklanish: {users['total']}\n"
        f"   • Sana: {now.strftime('%d.%m.%Y')}\n"
        f"   • Soat: {now.strftime('%H:%M')}\n\n"
        f"Statistika real vaqtda yangilanadi"
    )
    
    if edit:
        try:
            await message.edit_text(text, reply_markup=stats_kb())
        except:
            await message.answer(text, reply_markup=stats_kb())
    else:
        await message.answer(text, reply_markup=stats_kb())

@router.callback_query(F.data == "refresh_stats")
async def cb_refresh_stats(call: CallbackQuery):
    try:
        await show_stats(call.message, edit=True)
    except:
        await show_stats(call.message, edit=False)
    await call.answer("✅ Yangilandi!")

# ==================== QO'LLANMA ====================
@router.message(F.text.contains("Qo'llanma"))
async def cmd_guide(message: Message):
    from keyboards.user_kb import guide_kb
    guide_text = await get_setting("guide_text") or "Bot qo'llanmasi..."
    admin_username = await get_setting("admin_username") or "@admin"
    await message.answer(
        f"🤖 Bot qo'llanmasi 👇👇👇\n\n{guide_text}",
        reply_markup=guide_kb(admin_username)
    )

# ==================== REKLAMA ====================
@router.message(F.text.contains("Reklama"))
async def cmd_ads(message: Message):
    from keyboards.user_kb import ads_kb
    ads_text = await get_setting("ads_text") or "Reklama va homiylik uchun admin bilan bog'laning."
    admin_username = await get_setting("admin_username") or "@admin"
    ads_channel = await get_setting("ads_channel") or "@ads"
    await message.answer(
        f"💰 Reklama va Homiylik\n\n{ads_text}",
        reply_markup=ads_kb(admin_username, ads_channel)
    )

# ==================== BOT HAQIDA ====================
@router.message(F.text.contains("Bot haqida"))
async def cmd_about(message: Message):
    now = datetime.now()
    bot_username = await get_setting("bot_username") or "manhwa_bot"
    creator_username = await get_setting("creator_username") or "@creator"
    channel_username = await get_setting("channel_username") or "@channel"
    bot_version = await get_setting("bot_version") or "3.9"
    text = (
        f"🤖 Bot Haqida\n\n"
        f"🏷 Bot nomi: @{bot_username}\n"
        f"👨‍💻 Yaratuvchi: {creator_username}\n"
        f"📢 Kanal: {channel_username}\n"
        f"🔖 Versiya: {bot_version}\n"
        f"📅 Sana: {now.strftime('%d.%m.%Y')}"
    )
    await message.answer(text, reply_markup=about_kb())
