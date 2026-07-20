# admin/broadcast.py
import asyncio
import logging
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    get_all_users, get_anime, get_episodes, get_channels,
    get_setting, is_admin
)
from keyboards.admin_kb import (
    broadcast_target_kb, broadcast_type_kb,
    cancel_admin_kb, back_admin_kb, post_channels_kb, ep_post_channels_kb
)
from admin.anime_upload import send_anime_post
from config import config
from filters.admin_filter import IsAdminFilter

logger = logging.getLogger(__name__)
router = Router()

class BroadcastStates(StatesGroup):
    waiting_user_id = State()
    waiting_text = State()
    waiting_anime_code = State()
    waiting_post_link = State()
    # Post qilish
    waiting_post_code = State()

# ==================== XABAR YUBORISH ====================
@router.message(F.text == "✉️ Xabar yuborish", IsAdminFilter())
async def cmd_broadcast(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("📨 Kimga xabar yubormoqchisiz?", reply_markup=broadcast_target_kb())

@router.callback_query(F.data.startswith("bc_target:"))
async def cb_bc_target(call: CallbackQuery, state: FSMContext):
    target = call.data.split(":")[1]
    await state.update_data(bc_target=target)

    if target == "one":
        await state.set_state(BroadcastStates.waiting_user_id)
        await call.message.edit_text(
            "👤 Foydalanuvchi ID sini kiriting:",
            reply_markup=cancel_admin_kb()
        )
    else:
        target_names = {
            "all": "👥 Barcha foydalanuvchilarga",
            "vip": "💎 VIP foydalanuvchilarga",
            "normal": "⭐ Oddiy foydalanuvchilarga"
        }
        await call.message.edit_text(
            f"📨 {target_names.get(target, target)}\n\nQaysi usulda yuborasiz?",
            reply_markup=broadcast_type_kb(target)
        )

@router.message(BroadcastStates.waiting_user_id)
async def process_bc_user_id(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("❌ Noto'g'ri ID!", reply_markup=cancel_admin_kb())
        return
    await state.update_data(bc_user_id=uid)
    await message.answer(
        "📨 Qaysi usulda yuborasiz?",
        reply_markup=broadcast_type_kb("one")
    )

@router.callback_query(F.data.startswith("bc_type:"))
async def cb_bc_type(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    bc_type = parts[1]
    target = parts[2]
    await state.update_data(bc_type=bc_type, bc_target=target)

    if bc_type == "text":
        await state.set_state(BroadcastStates.waiting_text)
        await call.message.edit_text(
            "✍️ Xabarni yozing:\n\n(HTML formatini qo'llab-quvvatlaydi)",
            reply_markup=cancel_admin_kb(),
            parse_mode=None
        )
    elif bc_type == "code":
        await state.set_state(BroadcastStates.waiting_anime_code)
        await call.message.edit_text(
            "🔗 Manhwa kodini yuboring:\n\nMasalan: 50\n\n"
            "ℹ️ Bot bazadan topib, barcha userlarga yuboradi.",
            reply_markup=cancel_admin_kb(),
            parse_mode=None
        )
    elif bc_type == "link":
        await state.set_state(BroadcastStates.waiting_post_link)
        await call.message.edit_text(
            "🔗 Kanal postining linkini yuboring:\n\n"
            "Masalan: https://t.me/kanal_nomi/123\n\n"
            "ℹ️ Bot shu postni barcha userlarga forward qiladi (kanaldan ekani ko'rinadi).",
            reply_markup=cancel_admin_kb(),
            parse_mode=None
        )

async def get_recipients(target: str, bot_id: int = None):
    if target == "one":
        return []
    elif target == "all":
        return await get_all_users()
    elif target == "vip":
        return await get_all_users(vip_only=True)
    elif target == "normal":
        return await get_all_users(non_vip_only=True)
    return []

@router.message(BroadcastStates.waiting_text)
async def process_bc_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target = data["bc_target"]
    text = message.html_text
    await state.clear()

    if target == "one":
        uid = data.get("bc_user_id")
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            await message.answer("✅ Xabar yuborildi!", reply_markup=back_admin_kb())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=back_admin_kb())
        return

    users = await get_recipients(target)
    await message.answer(f"📤 {len(users)} ta foydalanuvchiga yuborilmoqda...")
    sent, failed = 0, 0
    for user in users:
        try:
            await bot.send_message(user["user_id"], text, parse_mode="HTML")
            sent += 1
        except:
            failed += 1
        await asyncio.sleep(config.BROADCAST_DELAY)
    await message.answer(
        f"✅ Broadcast tugadi!\n✅ Yuborildi: {sent}\n❌ Xato: {failed}",
        reply_markup=back_admin_kb()
    )

@router.message(BroadcastStates.waiting_anime_code)
async def process_bc_code(message: Message, state: FSMContext, bot: Bot):
    try:
        code = int(message.text.strip())
    except:
        await message.answer("❌ Faqat raqam!", reply_markup=cancel_admin_kb())
        return

    anime = await get_anime(code)
    if not anime:
        await message.answer("❌ Manhwa topilmadi!", reply_markup=cancel_admin_kb())
        return

    data = await state.get_data()
    target = data["bc_target"]
    await state.clear()

    episodes = await get_episodes(code)
    channels = await get_channels()
    ch = next((c for c in channels), None)

    if target == "one":
        uid = data.get("bc_user_id")
        try:
            bot_un = await get_setting("bot_username") or "manhwa_bot"
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            b = InlineKeyboardBuilder()
            b.button(text="🎬 Tomosha qilish", url=f"https://t.me/{bot_un}?start={code}")
            post_text = (
                f"✨ {anime['name']} ✨\n"
                f"📽 Boblar: {len(episodes)}\n"
                f"🔍 Kod: {code}"
            )
            if anime.get("poster_file_id"):
                await bot.send_photo(uid, photo=anime["poster_file_id"],
                                     caption=post_text, reply_markup=b.as_markup(), parse_mode=None)
            else:
                await bot.send_message(uid, post_text, reply_markup=b.as_markup(), parse_mode=None)
            await message.answer("✅ Yuborildi!", reply_markup=back_admin_kb())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=back_admin_kb())
        return

    users = await get_recipients(target)
    bot_un = await get_setting("bot_username") or "manhwa_bot"
    await message.answer(f"📤 {len(users)} ta foydalanuvchiga yuborilmoqda...")
    sent, failed = 0, 0
    for user in users:
        try:
            if anime.get("poster_file_id"):
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                b = InlineKeyboardBuilder()
                b.button(text="🎬 Tomosha qilish", url=f"https://t.me/{bot_un}")
                text = (
                    f"✨ {anime['name']} ✨\n"
                    f"📽 Boblar: {len(episodes)}\n"
                    f"🔍 Kod: {code}"
                )
                await bot.send_photo(user["user_id"], photo=anime["poster_file_id"],
                                     caption=text, reply_markup=b.as_markup(), parse_mode=None)
            sent += 1
        except:
            failed += 1
        await asyncio.sleep(config.BROADCAST_DELAY)
    await message.answer(f"✅ Tugadi! Yuborildi: {sent} | Xato: {failed}", reply_markup=back_admin_kb())

@router.message(BroadcastStates.waiting_post_link)
async def process_bc_link(message: Message, state: FSMContext, bot: Bot):
    link = message.text.strip()
    data = await state.get_data()
    target = data["bc_target"]
    await state.clear()

    # Link parse: https://t.me/channel/123
    try:
        parts = link.rstrip("/").split("/")
        msg_id = int(parts[-1])
        ch_username = parts[-2]
        if not ch_username.startswith("@"):
            ch_username = "@" + ch_username
    except:
        await message.answer("❌ Noto'g'ri link formati!", reply_markup=back_admin_kb())
        return

    if target == "one":
        uid = data.get("bc_user_id")
        try:
            await bot.forward_message(uid, ch_username, msg_id)
            await message.answer("✅ Yuborildi!", reply_markup=back_admin_kb())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=back_admin_kb())
        return

    users = await get_recipients(target)
    await message.answer(f"📤 {len(users)} ta foydalanuvchiga forward qilinmoqda...")
    sent, failed = 0, 0
    for user in users:
        try:
            await bot.forward_message(user["user_id"], ch_username, msg_id)
            sent += 1
        except:
            failed += 1
        await asyncio.sleep(config.BROADCAST_DELAY)
    await message.answer(f"✅ Tugadi! Yuborildi: {sent} | Xato: {failed}", reply_markup=back_admin_kb())

# ==================== POST QILISH ====================
@router.message(F.text == "📤 Post qilish", IsAdminFilter())
async def cmd_post(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(BroadcastStates.waiting_post_code)
    await state.update_data(selected_channels=[])
    await message.answer(
        "1️⃣2️⃣3️⃣4️⃣ Qaysi manhwa KODini kanalga yubormoqchisiz?\n\nMasalan: 147",
        reply_markup=cancel_admin_kb(),
        parse_mode=None
    )

@router.message(BroadcastStates.waiting_post_code)
async def process_post_code(message: Message, state: FSMContext):
    try:
        code = int(message.text.strip())
    except:
        await message.answer("❌ Faqat raqam!", reply_markup=cancel_admin_kb())
        return

    anime = await get_anime(code)
    if not anime:
        await message.answer("❌ Manhwa topilmadi!", reply_markup=cancel_admin_kb())
        return

    await state.update_data(post_anime_code=code, selected_channels=[])
    post_channels = await _get_post_channels()

    if not post_channels:
        await message.answer("❌ Asosiy kanallar yo'q! Avval kanal qo'shing.", reply_markup=back_admin_kb())
        return

    await message.answer(
        f"🎬 Anime: {anime['name']}\n\n"
        f"📡 Qaysi asosiy kanal(lar)ga post qilmoqchisiz?\nTanlang:",
        reply_markup=post_channels_kb(post_channels, []),
        parse_mode=None
    )

async def _get_post_channels():
    from database.db import get_main_channels
    post_channels = await get_main_channels()
    if not post_channels:
        channels = await get_channels()
        post_channels = [ch for ch in channels if ch["channel_type"] == "public"]
    return post_channels

@router.callback_query(F.data.startswith("toggle_ch:"))
async def cb_toggle_ch(call: CallbackQuery, state: FSMContext):
    ch_id = call.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("selected_channels", [])

    if ch_id in selected:
        selected.remove(ch_id)
    else:
        selected.append(ch_id)

    await state.update_data(selected_channels=selected)
    post_channels = await _get_post_channels()
    await call.message.edit_reply_markup(reply_markup=post_channels_kb(post_channels, selected))

@router.callback_query(F.data == "post_select_all")
async def cb_post_select_all(call: CallbackQuery, state: FSMContext):
    post_channels = await _get_post_channels()
    all_ids = [str(ch["channel_id"]) for ch in post_channels]
    await state.update_data(selected_channels=all_ids)
    await call.message.edit_reply_markup(reply_markup=post_channels_kb(post_channels, all_ids))

@router.callback_query(F.data == "post_send")
async def cb_post_send(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    code = data.get("post_anime_code")
    selected = data.get("selected_channels", [])

    if not selected:
        await call.answer("❌ Hech qanday kanal tanlanmadi!", show_alert=True)
        return

    anime = await get_anime(code)
    episodes = await get_episodes(code)
    channels = await get_channels()
    selected_channels = [ch for ch in channels if str(ch["channel_id"]) in selected]

    await state.clear()
    sent = 0
    for ch in selected_channels:
        try:
            await send_anime_post(bot, ch, anime, episodes)
            sent += 1
        except Exception as e:
            logger.error(f"Post xatolik: {e}")

    await call.message.edit_text(
        f"✅ Post yuborildi!\n📢 {sent} ta kanalga jo'natildi.",
        reply_markup=back_admin_kb()
    )

