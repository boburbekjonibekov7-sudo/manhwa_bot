# admin/channels.py
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_channels, add_channel, delete_channel, is_admin
from keyboards.admin_kb import (
    channels_menu_kb, required_channels_kb, main_channels_kb,
    channel_type_kb, channel_add_method_kb,
    back_admin_kb, cancel_admin_kb, back_cancel_admin_kb
)
import logging
from filters.admin_filter import IsAdminFilter

logger = logging.getLogger(__name__)
router = Router()

class ChannelStates(StatesGroup):
    waiting_id = State()
    waiting_link = State()
    waiting_post = State()
    waiting_url = State()
    waiting_private_forward = State()
    waiting_private_invite_link = State()

@router.message(F.text == "📡 Kanal boshqaruvi", IsAdminFilter())
async def cmd_channels(message: Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("📡 Kanal boshqaruvi:", reply_markup=channels_menu_kb())

@router.callback_query(F.data == "admin_channels")
async def cb_channels(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.edit_text("📡 Kanal boshqaruvi:", reply_markup=channels_menu_kb())
    except:
        await call.message.answer("📡 Kanal boshqaruvi:", reply_markup=channels_menu_kb())

@router.callback_query(F.data == "ch_required")
async def cb_ch_required(call: CallbackQuery):
    try:
        await call.message.edit_text("🔐 Majburiy obuna kanallar:", reply_markup=required_channels_kb())
    except:
        await call.message.answer("🔐 Majburiy obuna kanallar:", reply_markup=required_channels_kb())

@router.callback_query(F.data == "ch_main")
async def cb_ch_main(call: CallbackQuery):
    try:
        await call.message.edit_text("📢 Asosiy kanallar (post uchun):", reply_markup=main_channels_kb())
    except:
        await call.message.answer("📢 Asosiy kanallar (post uchun):", reply_markup=main_channels_kb())

# ==================== QO'SHISH ====================
@router.callback_query(F.data == "ch_add")
async def cb_ch_add(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("ch_type") != "main":
        await state.update_data(ch_type="public")
    await call.message.edit_text(
        "⚙️ Kanal turini tanlang:",
        reply_markup=channel_type_kb()
    )

@router.callback_query(F.data.startswith("ch_type:"))
async def cb_ch_type(call: CallbackQuery, state: FSMContext):
    ch_type = call.data.split(":")[1]
    data = await state.get_data()
    # Agar main kanal bo'lsa, ch_type ni "main" saqlab qolamiz
    if data.get("ch_type") == "main":
        await state.update_data(ch_type="main")
    else:
        await state.update_data(ch_type=ch_type)

    if ch_type == "url":
        await state.set_state(ChannelStates.waiting_url)
        await call.message.edit_text(
            "🔗 Havolani kiriting:\n\n"
            "Masalan: https://site.com yoki https://t.me/kanal\n\n"
            "Iltimos, to'g'ri formatda yuboring.",
            reply_markup=back_cancel_admin_kb("ch_add")
        )
    elif ch_type == "private_link":
        await state.set_state(ChannelStates.waiting_private_forward)
        await call.message.edit_text(
            "🔐 Shaxsiy/So'rovli kanal — 1-qadam\n\n"
            "A'zolikni haqiqatan tekshirish uchun bot kanal/guruhda "
            "ADMINISTRATOR bo'lishi shart.\n\n"
            "1. Botni ushbu kanal/guruhga administrator qilib qo'shing\n"
            "2. Keyin o'sha yerdan bitta postni (yoki istalgan xabarni) "
            "ushbu chatga FORWARD qiling\n\n"
            "Bot shu orqali kanalni aniqlaydi.",
            reply_markup=back_cancel_admin_kb("ch_add")
        )
    else:
        data2 = await state.get_data()
        saved_type = data2.get("ch_type", "public")
        back_cb2 = "ch_main" if saved_type == "main" else "ch_required"
        await call.message.edit_text(
            "📢 Ommaviy / Shaxsiy (Kanal · Guruh) - ulash\n\n"
            "Quyida kanal/guruhni ulashning 3 ta oddiy usuli mavjud:\n\n"
            "1. ID orqali ulash\n"
            "Kanal yoki guruh ID raqamini kiriting.\n"
            "ID odatda -100... shaklida bo'ladi.\n\n"
            "2. Havola orqali ulash\n"
            "Kanal/guruh havolasini yuboring.\n"
            "Masalan: @kanal_nomi yoki https://t.me/kanal\n\n"
            "3. Postni ulash orqali\n"
            "Kanal yoki guruhdan bitta postni ulashing va shu xabarni botga yuboring.",
            reply_markup=channel_add_method_kb(back_cb=back_cb2)
        )

@router.callback_query(F.data.startswith("ch_method:"))
async def cb_ch_method(call: CallbackQuery, state: FSMContext):
    method = call.data.split(":")[1]
    data = await state.get_data()
    ch_type = data.get("ch_type", "public")
    await state.update_data(ch_method=method, ch_type=ch_type)

    if method == "id":
        await state.set_state(ChannelStates.waiting_id)
        await call.message.edit_text(
            "🆔 Kanal yoki guruh ID sini kiriting:\n\n"
            "ID odatda -100... shaklida bo'ladi.",
            reply_markup=cancel_admin_kb()
        )
    elif method == "link":
        await state.set_state(ChannelStates.waiting_link)
        await call.message.edit_text(
            "🔗 Kanal/guruh havolasini yuboring:\n\n"
            "Masalan: @kanal_nomi yoki https://t.me/kanal",
            reply_markup=cancel_admin_kb()
        )
    elif method == "post":
        await state.set_state(ChannelStates.waiting_post)
        await call.message.edit_text(
            "📨 Kanal yoki guruhdan bitta postni forward qiling:\n\n"
            "Bot avtomatik ravishda kanalni taniydi.",
            reply_markup=cancel_admin_kb()
        )

@router.message(ChannelStates.waiting_id)
async def process_ch_id(message: Message, state: FSMContext, bot: Bot):
    try:
        ch_id = message.text.strip()
        chat = await bot.get_chat(ch_id)
        data = await state.get_data()
        ch_type = data.get("ch_type", "public")
        username = f"@{chat.username}" if chat.username else str(chat.id)
        is_main_val = 1 if ch_type == "main" else 0
        ch_db_type = "public" if ch_type in ("main",) else ch_type
        await add_channel(str(chat.id), username, chat.title, ch_db_type)
        if is_main_val:
            from database.db import set_main_channel
            await set_main_channel(str(chat.id), 1)
        back_cb = "ch_main" if ch_type == "main" else "ch_required"
        await state.clear()
        await message.answer(
            f"✅ Kanal qo'shildi!\n\n"
            f"📢 Nom: {chat.title}\n"
            f"🆔 ID: {chat.id}\n"
            f"👤 Username: {username}",
            reply_markup=back_admin_kb(back_cb)
        )
    except Exception as e:
        await message.answer(
            f"❌ Xatolik: {e}\n\nTo'g'ri ID kiriting.",
            reply_markup=cancel_admin_kb()
        )

@router.message(ChannelStates.waiting_link)
async def process_ch_link(message: Message, state: FSMContext, bot: Bot):
    try:
        link = message.text.strip()
        data = await state.get_data()
        ch_type = data.get("ch_type", "public")

        username = link.replace("https://t.me/", "@").replace("http://t.me/", "@")
        if not username.startswith("@"):
            username = "@" + username
        chat = await bot.get_chat(username)
        uname = f"@{chat.username}" if chat.username else username
        is_main_val = 1 if ch_type == "main" else 0
        # public ham "public" tipida saqlanadi
        ch_db_type = "public"
        await add_channel(str(chat.id), uname, chat.title, ch_db_type)
        if is_main_val:
            from database.db import set_main_channel
            await set_main_channel(str(chat.id), 1)
        back_cb = "ch_main" if ch_type == "main" else "ch_required"
        await state.clear()
        await message.answer(
            f"✅ Kanal qo'shildi!\n\n"
            f"📢 Nom: {chat.title}\n"
            f"🆔 ID: {chat.id}",
            reply_markup=back_admin_kb(back_cb)
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}", reply_markup=cancel_admin_kb())

@router.message(ChannelStates.waiting_private_forward)
async def process_private_forward(message: Message, state: FSMContext, bot: Bot):
    """1-qadam: Forward orqali haqiqiy chat_id ni olamiz."""
    if not message.forward_from_chat:
        await message.answer(
            "❌ Bu forward xabar emas.\n\n"
            "Iltimos, kanal/guruhdan bitta xabarni forward qiling "
            "(bot o'sha yerda admin bo'lishi kerak).",
            reply_markup=cancel_admin_kb()
        )
        return

    chat = message.forward_from_chat

    # Bot chatda a'zo/admin ekanini tekshiramiz — aks holda keyinchalik
    # get_chat_member ishlamaydi.
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat.id, me.id)
        if member.status not in ("administrator", "creator", "member"):
            raise ValueError("bot a'zo emas")
    except Exception:
        await message.answer(
            f"❌ Bot \"{chat.title}\" da hali administrator emas.\n\n"
            f"Avval botni o'sha kanal/guruhga administrator qilib qo'shing, "
            f"so'ng qaytadan shu yerdan xabarni forward qiling.",
            reply_markup=cancel_admin_kb()
        )
        return

    await state.update_data(private_chat_id=str(chat.id), private_chat_title=chat.title)
    await state.set_state(ChannelStates.waiting_private_invite_link)
    await message.answer(
        f"✅ Kanal aniqlandi: {chat.title}\n\n"
        f"🔐 Shaxsiy/So'rovli kanal — 2-qadam\n\n"
        f"Endi ushbu kanalning taklif (invite) havolasini yuboring — "
        f"bu havola foydalanuvchilarga ko'rsatiladi.\n\n"
        f"Masalan: https://t.me/+AbCdEfGhIjKl",
        reply_markup=cancel_admin_kb()
    )

@router.message(ChannelStates.waiting_private_invite_link)
async def process_private_invite_link(message: Message, state: FSMContext):
    """2-qadam: Ko'rsatish uchun invite link, tekshirish esa haqiqiy chat_id orqali."""
    link = message.text.strip()
    if not link.startswith("http"):
        await message.answer("❌ To'g'ri havola kiriting (https:// bilan boshlanishi kerak).", reply_markup=cancel_admin_kb())
        return

    data = await state.get_data()
    chat_id = data.get("private_chat_id")
    chat_title = data.get("private_chat_title", "Shaxsiy/So'rovli kanal")
    ch_type = data.get("ch_type", "public")

    if not chat_id:
        await message.answer("❌ Xatolik: kanal aniqlanmagan. Qaytadan boshlang.", reply_markup=cancel_admin_kb())
        await state.clear()
        return

    is_main_val = 1 if ch_type == "main" else 0
    # channel_type="private" — bu turi check_subscription tekshiruviga KIRADI,
    # chunki chat_id haqiqiy (forward orqali olingan), invite link emas.
    await add_channel(chat_id, link, chat_title, "private", link)
    if is_main_val:
        from database.db import set_main_channel
        await set_main_channel(chat_id, 1)

    back_cb = "ch_main" if ch_type == "main" else "ch_required"
    await state.clear()
    await message.answer(
        f"✅ Shaxsiy/So'rovli kanal qo'shildi!\n\n"
        f"📢 Nom: {chat_title}\n"
        f"🆔 ID: {chat_id}\n"
        f"🔗 Havola: {link}\n\n"
        f"✅ A'zolik endi haqiqatan tekshiriladi:\n"
        f"• Agar kanalda \"so'rovli qo'shilish\" yoqilgan bo'lsa — "
        f"foydalanuvchi so'rov yuborishi YETARLI (siz tasdiqlashingizni "
        f"kutmaydi).\n"
        f"• Agar oddiy a'zolik bo'lsa — to'liq a'zo bo'lishi kerak.",
        reply_markup=back_admin_kb(back_cb)
    )

@router.message(ChannelStates.waiting_post)
async def process_ch_post(message: Message, state: FSMContext):
    try:
        if message.forward_from_chat:
            chat = message.forward_from_chat
            data = await state.get_data()
            ch_type = data.get("ch_type", "public")
            username = f"@{chat.username}" if chat.username else str(chat.id)
            is_main_val = 1 if ch_type == "main" else 0
            await add_channel(str(chat.id), username, chat.title, "public" if ch_type == "main" else ch_type)
            if is_main_val:
                from database.db import set_main_channel
                await set_main_channel(str(chat.id), 1)
            back_cb = "ch_main" if ch_type == "main" else "ch_required"
            await state.clear()
            await message.answer(
                f"✅ Kanal qo'shildi!\n\n"
                f"📢 Nom: {chat.title}\n"
                f"🆔 ID: {chat.id}",
                reply_markup=back_admin_kb(back_cb)
            )
        else:
            await message.answer("❌ Bu forward xabar emas. Kanaldan post yuboring.", reply_markup=cancel_admin_kb())
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}", reply_markup=cancel_admin_kb())

@router.message(ChannelStates.waiting_url)
async def process_ch_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("❌ To'g'ri URL kiriting. (https://...)", reply_markup=cancel_admin_kb())
        return
    await add_channel(url, url, url, "url", url)
    await state.clear()
    await message.answer(
        f"✅ Havola qo'shildi!\n🔗 {url}",
        reply_markup=back_admin_kb("ch_required")
    )

# ==================== RO'YXAT ====================
@router.callback_query(F.data == "ch_list")
async def cb_ch_list(call: CallbackQuery):
    channels = await get_channels()
    req_chs = [ch for ch in channels if not ch.get("is_main")]
    if not req_chs:
        await call.message.edit_text(
            "📋 Majburiy obuna kanallar bo'sh.",
            reply_markup=back_admin_kb("ch_required")
        )
        return
    text = "📡 Kanallar ro'yxati:\n\n"
    for i, ch in enumerate(req_chs, 1):
        username = ch.get("channel_username") or ""
        url = ch.get("channel_url") or ""
        name = ch.get("channel_name") or username or url
        display = username if username else url
        ch_type = ch.get("channel_type", "")
        type_icon = "🔐" if "private" in ch_type else "📢"
        text += f"{i}. {display} | {type_icon}\n"
    text += f"\nUlangan kanallar soni: {len(req_chs)} ta"
    await call.message.edit_text(text, reply_markup=back_admin_kb("ch_required"))

# ==================== O'CHIRISH ====================
@router.callback_query(F.data == "ch_delete")
async def cb_ch_delete(call: CallbackQuery):
    channels = await get_channels()
    req_chs = [ch for ch in channels if not ch.get("is_main")]
    if not req_chs:
        await call.answer("❌ Majburiy obuna kanallar yo'q!", show_alert=True)
        return
    text = "✂️ O'chirish uchun raqamni tanlang:\n\n"
    for i, ch in enumerate(req_chs, 1):
        username = ch.get("channel_username") or ""
        url = ch.get("channel_url") or ""
        display = username if username else url
        ch_type = ch.get("channel_type", "")
        type_word = "request" if "private" in ch_type else "lock"
        text += f"{i}. {display} | {type_word}\n"
    text += f"\nUlangan kanallar soni: {len(req_chs)} ta"
    # Inline tugmalar - raqam bilan
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    for i, ch in enumerate(req_chs, 1):
        b.button(text=f"🗑 {i}", callback_data=f"ch_del_confirm:{ch['id']}")
    b.button(text="🔙 Orqaga", callback_data="ch_required")
    b.adjust(5)
    await call.message.edit_text(text, reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("ch_del_confirm:"))
async def cb_ch_del_confirm(call: CallbackQuery):
    ch_db_id = int(call.data.split(":")[1])
    channels = await get_channels()
    ch = next((c for c in channels if c["id"] == ch_db_id), None)
    if not ch:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="✅ Ha, o'chirish", callback_data=f"ch_del_do:{ch['channel_id']}")
    b.button(text="❌ Yo'q", callback_data="ch_delete")
    b.adjust(2)
    await call.message.edit_text(
        f"❓ O'chirishni tasdiqlaysizmi?\n{ch['channel_name'] or ch['channel_username']}",
        reply_markup=b.as_markup()
    )

@router.callback_query(F.data.startswith("ch_del_do:"))
async def cb_ch_del_do(call: CallbackQuery):
    ch_id = call.data.split(":")[1]
    await delete_channel(ch_id)
    from keyboards.admin_kb import required_channels_kb
    await call.message.edit_text(
        "✅ Kanal o'chirildi!",
        reply_markup=back_admin_kb("ch_required")
    )


# ==================== ASOSIY KANALLAR ====================
@router.callback_query(F.data == "main_ch_add")
async def cb_main_ch_add(call: CallbackQuery, state: FSMContext):
    await state.update_data(ch_type="main", ch_method=None)
    await call.message.edit_text(
        "📢 Asosiy kanal qo'shish\n\nQanday ulash?",
        reply_markup=channel_add_method_kb(back_cb="ch_main")
    )

@router.callback_query(F.data == "main_ch_list")
async def cb_main_ch_list(call: CallbackQuery):
    from database.db import get_main_channels
    channels = await get_main_channels()
    if not channels:
        await call.message.edit_text(
            "📋 Asosiy kanallar yo'q.",
            reply_markup=back_admin_kb("ch_main")
        )
        return
    text = "📢 Asosiy kanallar:\n\n"
    for ch in channels:
        text += f"• {ch['channel_name'] or ch['channel_username']}\n"
    await call.message.edit_text(text, reply_markup=back_admin_kb("ch_main"))

@router.callback_query(F.data == "main_ch_delete")
async def cb_main_ch_delete(call: CallbackQuery):
    from database.db import get_main_channels
    channels = await get_main_channels()
    if not channels:
        await call.answer("❌ Asosiy kanallar yo'q!", show_alert=True)
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    for ch in channels:
        b.button(
            text=f"🗑 {ch['channel_name'] or ch['channel_username']}",
            callback_data=f"main_ch_del_do:{ch['channel_id']}"
        )
    b.button(text="🔙 Orqaga", callback_data="ch_main")
    b.adjust(1)
    await call.message.edit_text("🗑 O'chirish uchun kanalni tanlang:", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("main_ch_del_do:"))
async def cb_main_ch_del_do(call: CallbackQuery):
    from database.db import delete_channel
    ch_id = call.data.split(":")[1]
    await delete_channel(ch_id)
    await call.message.edit_text("✅ Asosiy kanal o'chirildi!", reply_markup=back_admin_kb("ch_main"))
