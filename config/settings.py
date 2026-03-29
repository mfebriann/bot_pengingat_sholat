"""
Application configuration loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Centralized application settings."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "339890451"))

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/prayer_bot"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Aladhan API
    ALADHAN_BASE_URL: str = "http://api.aladhan.com/v1"

    # Cache TTL (seconds) — 24 hours
    CACHE_TTL: int = 86400

    # Reminder lead time (minutes)
    REMINDER_BEFORE_MINUTES: int = 10

    # Prayer names we track
    PRAYER_NAMES: list[str] = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

    # Indonesian prayer name mapping for display
    PRAYER_DISPLAY_NAMES: dict[str, str] = {
        "Fajr": "Subuh",
        "Dhuhr": "Dzuhur",
        "Asr": "Ashar",
        "Maghrib": "Maghrib",
        "Isha": "Isya",
    }


settings = Settings()
