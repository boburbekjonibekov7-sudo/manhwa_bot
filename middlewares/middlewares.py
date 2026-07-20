# middlewares/middlewares.py
import asyncio
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from database.db import get_user, add_user, is_admin, get_setting
from config import config
import logging

logger = logging.getLogger(__name__)

# ==================== THROTTLING ====================
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self._cache: Dict[int, float] = {}

    async def __call__(self, handler, event: TelegramObject, data: Dict[str, Any]):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        
        now = time.time()
        last = self._cache.get(user.id, 0)
        
        if now - last < self.rate_limit:
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("⚠️ Iltimos, biroz kuting!", show_alert=False)
                except:
                    pass
            return
        
        self._cache[user.id] = now
        # Cache tozalash (memory leak oldini olish)
        if len(self._cache) > 10000:
            cutoff = now - 60
            self._cache = {k: v for k, v in self._cache.items() if v > cutoff}
        
        return await handler(event, data)

# ==================== USER REGISTER + BAN ====================
class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: Dict[str, Any]):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        
        # Register user
        await add_user(user.id, user.username, user.full_name)
        
        # Check ban
        db_user = await get_user(user.id)
        if db_user and db_user["is_banned"] and not await is_admin(user.id):
            if isinstance(event, Message):
                await event.answer("🚫 Siz botdan bloklangansiz.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Siz botdan bloklangansiz.", show_alert=True)
            return
        
        # Check bot active
        bot_active = await get_setting("bot_active")
        if bot_active == "0" and not await is_admin(user.id):
            if isinstance(event, Message):
                await event.answer("🔧 Bot hozir texnik ishlar uchun to'xtatilgan. Tez orada qayta ishga tushadi.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🔧 Bot hozir to'xtatilgan.", show_alert=True)
            return
        
        data["db_user"] = db_user
        return await handler(event, data)

# ==================== VIP EXPIRY CHECK ====================
class VipCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: Dict[str, Any]):
        from database.db import check_vip_expiry
        # Har 100 ta so'rovda bir marta tekshirish
        import random
        if random.random() < 0.01:
            await check_vip_expiry()
        return await handler(event, data)
