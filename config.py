# config.py
import os
from dataclasses import dataclass, field

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8615878852:AAFenGE5RnwTBl5bPEOjzm1owxaNU86n2TA")
    ADMIN_IDS: list = None
    DB_PATH: str = "manhwa_bot.db"

    # Rate limiting
    RATE_LIMIT: float = 0.5        # seconds between messages
    BROADCAST_DELAY: float = 0.05  # seconds between broadcast messages

    # Pagination
    EPISODES_PER_PAGE: int = 24
    ANIMES_PER_PAGE: int = 8

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = [
                int(x) for x in os.getenv("ADMIN_IDS", "8720175870").split(",")
            ]

config = Config()
