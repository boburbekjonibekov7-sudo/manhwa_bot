# config.py
import os
from dataclasses import dataclass, field

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "TOKEN")
    ADMIN_IDS: list = None
    DB_PATH: str = "manhwa_bot.db"

    # Rate limiting
    RATE_LIMIT: float = 0.5        # seconds between messages
    BROADCAST_DELAY: float = 0.05  # seconds between broadcast messages

    # Pagination
    EPISODES_PER_PAGE: int = 24
    ANIMES_PER_PAGE: int = 8

    # Webhook settings (built-in defaults, no env var needed)
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "manhwa_webhook_2025")
    PORT: int = int(os.getenv("PORT", "8000"))
    WEBHOOK_PATH: str = ""

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = [
                int(x) for x in os.getenv("ADMIN_IDS", "8720175870").split(",")
            ]
        # Set webhook path after secret is resolved
        self.WEBHOOK_PATH = f"/webhook/{self.WEBHOOK_SECRET}"

config = Config()
