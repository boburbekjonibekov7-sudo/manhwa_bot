# admin/anime_upload.py
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    add_anime, get_anime, add_episode, add_season,
    get_episodes, get_channels, get_setting, is_admin
)
from keyboards.admin_kb import skip_kb, cancel_admin_kb, back_admin_kb
from config import config
import logging
from filters.admin_filter import IsAdminFilter

logger = logging.getLogger(__name__)
router = Router()

class AnimeUploadStates(StatesGroup):
    waiting_code = State()
    waiting_name = State()
    waiting_genre = State()
    waiting_studio = State()
    waiting_poster = State()
    waiting_episodes = State()


@router.message(F.text == "🎬 Manhwa yuklash", IsAdminFilter())
async def cmd_anime_upload(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()

    auto_code = await get_setting("auto_code") or "1"
    if auto_code == "1":
        from database.db import get_next_available_code
        next_code = await get_next_available_code()
        await state.update_data(code=next_code)
        await state.set_state(AnimeUploadStates.waiting_name)
        await message.answer(
            f"🔢 Auto kod: {next_code}\n\n"
            f"📝 Manhwa nomini kiriting:",
            reply_markup=cancel_admin_kb(),
            parse_mode=None
        )
    else:
        await state.set_state(AnimeUploadStates.waiting_code)
        await message.answer(
            "1️⃣2️⃣3️⃣4️⃣ Manhwa kodini kiriting:\n(Masalan: 101, 205)",
            reply_markup=cancel_admin_kb(),
            parse_mode=None
        )

@router.message(AnimeUploadStates.waiting_code)
async def process_code(message: Message, state: FSMContext):
    try:
        code = int(message.text.strip())
    except:
        await message.answer("❌ Faqat raqam kiriting!", reply_markup=cancel_admin_kb())
        return

    existing = await get_anime(code)
    if existing:
        await message.answer(
            f"❌ {code} kod allaqachon mavjud: {existing['name']}\nBoshqa kod kiriting.",
            reply_markup=cancel_admin_kb(),
            parse_mode=None
        )
        return

    await state.update_data(code=code)
    await state.set_state(AnimeUploadStates.waiting_name)
    await message.answer(
        "📝 Manhwa nomini kiriting:",
        reply_markup=cancel_admin_kb()
    )

@router.message(AnimeUploadStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AnimeUploadStates.waiting_genre)
    await message.answer(
        "🎭 Manhwa janrini kiriting:\n(Masalan: Action, Comedy)\n\n/skip - o'tkazib yuborish",
        reply_markup=skip_kb("skip_genre"),
        parse_mode=None
    )

@router.message(AnimeUploadStates.waiting_genre)
async def process_genre(message: Message, state: FSMContext):
    if message.text.strip() != "/skip":
        await state.update_data(genre=message.text.strip())
    else:
        await state.update_data(genre=None)
    await ask_studio(message, state)

@router.callback_query(F.data == "skip_genre")
async def cb_skip_genre(call: CallbackQuery, state: FSMContext):
    await state.update_data(genre=None)
    await ask_studio(call.message, state)

async def ask_studio(message, state: FSMContext):
    await state.set_state(AnimeUploadStates.waiting_studio)
    await message.answer(
        "🎙 Ovoz bergan studiya:\n\n/skip - o'tkazib yuborish",
        reply_markup=skip_kb("skip_studio")
    )

@router.message(AnimeUploadStates.waiting_studio)
async def process_studio(message: Message, state: FSMContext):
    if message.text.strip() != "/skip":
        await state.update_data(studio=message.text.strip())
    else:
        await state.update_data(studio=None)
    await ask_poster(message, state)

@router.callback_query(F.data == "skip_studio")
async def cb_skip_studio(call: CallbackQuery, state: FSMContext):
    await state.update_data(studio=None)
    await ask_poster(call.message, state)

async def ask_poster(message, state: FSMContext):
    await state.set_state(AnimeUploadStates.waiting_poster)
    await message.answer(
        "🎬 Posterni yuboring (Rasm/Video).",
        reply_markup=cancel_admin_kb()
    )

@router.message(AnimeUploadStates.waiting_poster)
async def process_poster(message: Message, state: FSMContext):
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.animation:
        file_id = message.animation.file_id
    else:
        await message.answer("❌ Rasm yoki video yuboring!", reply_markup=cancel_admin_kb())
        return

    await state.update_data(poster_file_id=file_id, season=1, episodes=[])
    data = await state.get_data()

    # Anime saqlash
    await add_anime(
        data["code"], data["name"],
        data.get("genre"), data.get("studio"), file_id
    )
    await add_season(data["code"], 1)

    await state.set_state(AnimeUploadStates.waiting_episodes)
    await message.answer(
        f"✅ Manhwa ma'lumotlari saqlandi!\n\n"
        f"📤 Endi boblarni yuboring (video yoki PDF).\n"
        f"Bir safarda bir necha fayl yuborsangiz ham barchasini qabul qilaman.\n"
        f"Tugatgach: /done deb yozing.",
        reply_markup=cancel_admin_kb()
    )


@router.message(AnimeUploadStates.waiting_episodes, F.text == "/done")
async def process_done(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    code = data["code"]
    anime = await get_anime(code)
    episodes = await get_episodes(code)

    await state.clear()

    text = (
        f"✅ Manhwa saqlandi!\n"
        f"📌 Kod: {code}\n"
        f"📺 Nomi: {anime['name']}\n"
        f"📁 Tur: 🔴 Oddiy\n"
        f"📦 Jami: {len(episodes)} bob."
    )
    await message.answer(text, reply_markup=back_admin_kb())

    # Auto post
    auto_post = await get_setting("auto_post")
    if auto_post == "1":
        from database.db import get_main_channels
        post_channels = await get_main_channels()
        if not post_channels:
            channels = await get_channels()
            post_channels = [ch for ch in channels if ch["channel_type"] == "public"]
        sent = 0
        for ch in post_channels:
            try:
                await send_anime_post(bot, ch, anime, episodes)
                sent += 1
            except Exception as e:
                logger.error(f"Post xatolik {ch['channel_id']}: {e}")
        if sent:
            await message.answer(f"📢 Auto post: {sent} ta kanalga yuborildi.")


async def _save_episode(code: int, season: int, message: Message, bot: Bot):
    """Video yoki PDF faylni episode sifatida saqlash"""
    file_type = None
    file_id = None
    file_name = None

    if message.video:
        file_type = "video"
        file_id = message.video.file_id
    elif message.document:
        doc = message.document
        is_pdf = (doc.mime_type == "application/pdf") or (doc.file_name and doc.file_name.lower().endswith(".pdf"))
        if not is_pdf:
            return  # Skip non-PDF silently
        file_type = "pdf"
        file_id = doc.file_id
        file_name = doc.file_name
    else:
        return  # Skip unknown type

    # Episode raqamini aniqlash
    episodes = await get_episodes(code, season)
    ep_num = len(episodes) + 1

    # Database'ga saqlash
    await add_episode(code, season, ep_num, file_id, file_type=file_type, file_name=file_name)

    # Javob berish — faqat media group bo'lmagan yoki oxirgi fayl uchun
    type_label = "video" if file_type == "video" else "PDF"
    await message.answer(f"✅ {ep_num}-bob qo'shildi ({type_label}).")


@router.message(AnimeUploadStates.waiting_episodes, F.video | F.document)
async def process_episode(message: Message, state: FSMContext, bot: Bot):
    """Har qanday video yoki PDF faylni qabul qilish — cheklovsiz, ketma-ket yoki media group"""
    data = await state.get_data()
    code = data["code"]
    season = data.get("season", 1)

    # Document bo'lsa, PDF ekanini tekshirish
    if message.document:
        doc = message.document
        is_pdf = (doc.mime_type == "application/pdf") or (doc.file_name and doc.file_name.lower().endswith(".pdf"))
        if not is_pdf:
            # PDF emas — xato xabari
            await message.answer(
                "❌ Faqat video yoki PDF fayl qabul qilinadi.\n"
                "Boshqa turdagi hujjat yuborilmagan."
            )
            return

    await _save_episode(code, season, message, bot)


async def send_anime_post(bot, channel: dict, anime: dict, episodes: list):
    ch_username = channel.get("channel_username", "")
    genre = anime.get("genre") or "Manhwa"
    text = (
        f"——————————————\n"
        f"✨ {anime['name']} ✨\n"
        f"——————————————\n"
        f"📽 Boblar soni : {len(episodes)}\n"
        f"✏️ Janri : {genre}\n"
        f"☁️ Tili : Ozbek\n"
        f"🔍 Kod : {anime['code']}\n"
        f"🌐 Manzil: {ch_username}\n"
        f"——————————————"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    bot_username = await get_setting("bot_username") or "manhwa_bot"
    b.button(text="💎 Tomosha qilish 💎", url=f"https://t.me/{bot_username}?start={anime['code']}")

    ch_id = channel["channel_id"]
    if anime.get("poster_file_id"):
        await bot.send_photo(
            ch_id,
            photo=anime["poster_file_id"],
            caption=text,
            reply_markup=b.as_markup(),
            parse_mode=None
        )
    else:
        await bot.send_message(ch_id, text, reply_markup=b.as_markup(), parse_mode=None)
