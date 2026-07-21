# main.py (TO'LIQ WEBHOOK REJIMI)
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import config
from database.db import init_db, check_vip_expiry
from middlewares.middlewares import ThrottlingMiddleware, UserMiddleware, VipCheckMiddleware

# Routers
from admin.panel import router as admin_panel_router
from admin.channels import router as channels_router
from admin.anime_upload import router as anime_upload_router
from admin.anime_edit import router as anime_edit_router
from admin.broadcast import router as broadcast_router
from admin.bot_panel import router as bot_panel_router
from admin.guide import router as guide_router
from user.start import router as start_router
from user.anime import router as anime_router
from user.vip import router as vip_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def vip_checker():
    while True:
        await asyncio.sleep(1800)
        try:
            await check_vip_expiry()
        except Exception as e:
            logger.error(f"VIP checker xatolik: {e}")

async def on_startup(bot: Bot):
    await init_db()
    await check_vip_expiry()
    asyncio.create_task(vip_checker())

    # Webhook URL yaratish va Telegram'ga o'rnatish
    base_url = os.getenv("RENDER_EXTERNAL_URL")
    if base_url:
        webhook_url = f"{base_url.rstrip('/')}{config.WEBHOOK_PATH}"
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info(f"🌐 Telegram Webhook muvaffaqiyatli o'rnatildi: {webhook_url}")
    else:
        logger.error("❌ RENDER_EXTERNAL_URL topilmadi! Render Environment Variables-ga o'z domeningizni qo'shing.")

async def main():
    token = config.BOT_TOKEN
    if not token or token == "TOKEN" or len(token) < 20:
        logger.error("❌ BOT_TOKEN noto'g'ri!")
        sys.exit(1)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares & Routers
    dp.message.middleware(ThrottlingMiddleware(rate_limit=config.RATE_LIMIT))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.3))
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.message.middleware(VipCheckMiddleware())

    dp.include_router(admin_panel_router)
    dp.include_router(channels_router)
    dp.include_router(anime_upload_router)
    dp.include_router(anime_edit_router)
    dp.include_router(broadcast_router)
    dp.include_router(bot_panel_router)
    dp.include_router(guide_router)
    dp.include_router(start_router)
    dp.include_router(anime_router)
    dp.include_router(vip_router)

    app = web.Application()

    # Health check (Render port scan uchun)
    async def health_check(request):
        return web.Response(text="OK")

    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    # Webhook handler
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=config.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # Startup hodisasini ulash
    dp.startup.register(on_startup)

    # Serverni ishga tushirish
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()

    logger.info(f"✅ Web server 0.0.0.0:{config.PORT} portida ishlamoqda")

    try:
        await asyncio.Event().wait()
    finally:
        await bot.session.close()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
