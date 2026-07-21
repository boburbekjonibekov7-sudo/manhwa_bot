# config.py
import os
from dataclasses import dataclass, field

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "TOKEN")
    ADMIN_IDS: list[int] = field(default_factory=list)
    DB_PATH: str = "manhwa_bot.db"

    # Rate limiting
    RATE_LIMIT: float = 0.5         # seconds between messages
    BROADCAST_DELAY: float = 0.05   # seconds between broadcast messages

    # Pagination
    EPISODES_PER_PAGE: int = 24
    ANIMES_PER_PAGE: int = 8

    # Webhook settings
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "manhwa_webhook_2025")
    PORT: int = int(os.getenv("PORT", "8000"))
    WEBHOOK_PATH: str = field(init=False)  # __post_init__ da dinamik hisoblanadi

    def __post_init__(self):
        # ADMIN_IDS tekshiruvi
        if not self.ADMIN_IDS:
            admin_env = os.getenv("ADMIN_IDS", "8720175870")
            self.ADMIN_IDS = [int(x.strip()) for x in admin_env.split(",") if x.strip().isdigit()]

        # Webhook path xavfsiz o'rnatilishi
        self.WEBHOOK_PATH = f"/webhook/{self.WEBHOOK_SECRET}"

config = Config()
