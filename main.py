# main.py
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

# ==================== ROUTERS ====================
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

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== VIP CHECKER ====================
async def vip_checker():
    """Har 30 daqiqada VIP muddati tugagan userlarni tozalash"""
    while True:
        await asyncio.sleep(1800)
        try:
            await check_vip_expiry()
            logger.info("VIP expiry check completed")
        except Exception as e:
            logger.error(f"VIP checker xatolik: {e}")


# ==================== STARTUP ====================
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await init_db()
    logger.info("✅ Database initialized")
    await check_vip_expiry()
    logger.info("✅ VIP expiry checked on startup")
    asyncio.create_task(vip_checker())
    logger.info("✅ VIP checker task started")

    # Set webhook to Telegram
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔄 Eski webhook o'chirildi")
    except Exception as e:
        logger.warning(f"Webhook o'chirishda xatolik: {e}")

    # Log the webhook URL for debugging
    webhook_base = os.getenv("RENDER_EXTERNAL_URL", os.getenv("RENDER_SERVICE_URL", ""))
    if webhook_base:
        webhook_url = f"{webhook_base}{config.WEBHOOK_PATH}"
        logger.info(f"🌐 Webhook URL: {webhook_url}")

    logger.info("🚀 Bot muvaffaqiyatli ishga tushdi (webhook rejimi)!")


# ==================== MAIN ====================
async def main():
    # Validate token before creating bot
    token = config.BOT_TOKEN
    if not token or token == "TOKEN" or len(token) < 20:
        logger.error("❌ BOT_TOKEN noto'g'ri yoki bo'sh! Render dashboard'da Environment Variables ga to'g'ri token qo'shing.")
        sys.exit(1)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # --- Middlewares (tartib muhim: Throttling → User → VipCheck) ---
    dp.message.middleware(ThrottlingMiddleware(rate_limit=config.RATE_LIMIT))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.3))
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.message.middleware(VipCheckMiddleware())

    # --- Routers (admin avval — F.text == ... konfliktini hal qilish uchun) ---
    dp.include_router(admin_panel_router)    # /admin command, admin_panel callback
    dp.include_router(channels_router)       # Kanal boshqaruvi
    dp.include_router(anime_upload_router)   # Anime yuklash
    dp.include_router(anime_edit_router)     # Kodlar paneli, anime tahrirlash
    dp.include_router(broadcast_router)      # Xabar yuborish, post qilish
    dp.include_router(bot_panel_router)      # Bot paneli, VIP, adminlar, statistika
    dp.include_router(guide_router)          # Qo'llanma, kodlar ro'yxati
    # User routerlar oxirida
    dp.include_router(start_router)          # /start, asosiy menyu
    dp.include_router(anime_router)          # Anime izlash, tomosha qilish
    dp.include_router(vip_router)            # VIP sotib olish, promokod

    dp.startup.register(on_startup, bot=bot)

    logger.info("🚀 Web server ishga tushmoqda...")

    # --- Webhook server setup ---
    app = web.Application()

    # Health check endpoint
    async def health_check(request):
        return web.Response(text="OK")

    app.router.add_get("/health", health_check)

    # Register webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)

    # Setup application lifecycle
    setup_application(app, dp, bot=bot)

    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()

    logger.info(f"✅ Server ishga tushdi: http://0.0.0.0:{config.PORT}")

    # Keep server running
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
    finally:
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
