# filters/admin_filter.py
from aiogram.filters import BaseFilter
from aiogram.types import Message
from database.db import is_admin


class IsAdminFilter(BaseFilter):
    """
    Handler faqat admin bo'lganda ishga tushishi kerak bo'lgan joylarda ishlatiladi.
    Agar False qaytarsa, aiogram avtomatik ravishda keyingi mos router/handlerga
    o'tadi (masalan user/start.py dagi haqiqiy user handleriga) — shu orqali
    matn bir xil bo'lgan admin/user tugmalari (masalan "📊 Statistika")
    bir-birini "band" qilib qo'ymaydi.
    """
    async def __call__(self, message: Message) -> bool:
        return await is_admin(message.from_user.id)
