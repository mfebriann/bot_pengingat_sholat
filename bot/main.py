"""
Bot entry point — initializes the database and starts Telegram polling.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config.settings import settings
from models.base import init_db
from bot.handlers import (
    start_handler,
    help_handler,
    province_callback_handler,
    jadwal_handler,
    feedback_handler,
    quote_handler,
    info_handler,
    error_handler,
    test_reminder_handler,
)
from utils.logger import setup_logger

logger = setup_logger("bot.main")


def main():
    """Build and run the Telegram bot."""

    # Validate token
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "your_bot_token_here":
        logger.error("TELEGRAM_BOT_TOKEN is not set! Please configure .env file.")
        print("❌ Error: TELEGRAM_BOT_TOKEN belum di-set.")
        print("   Silakan copy .env.example ke .env dan isi bot token Anda.")
        sys.exit(1)

    # Initialize database tables
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        print(f"❌ Error: Gagal mengkoneksikan database — {e}")
        print("   Pastikan PostgreSQL berjalan dan DATABASE_URL di .env benar.")
        sys.exit(1)

    # Build the Telegram application
    logger.info("Building Telegram bot application...")

    # Workaround for python-telegram-bot 21.3: Application defines __slots__ but is missing
    # the slot for __stop_running_marker (crashes on Python 3.13 during Application.__init__).
    # Prefer upgrading/downgrading python-telegram-bot; this keeps the bot runnable meanwhile.
    try:
        app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    except AttributeError as e:
        if "__stop_running_marker" not in str(e):
            raise

        class PatchedApplication(Application):
            __slots__ = ("_Application__stop_running_marker", "__weakref__")

        app = (
            ApplicationBuilder()
            .application_class(PatchedApplication)
            .token(settings.TELEGRAM_BOT_TOKEN)
            .build()
        )

    # Register command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("jadwal", jadwal_handler))
    app.add_handler(CommandHandler("feedback", feedback_handler))
    app.add_handler(CommandHandler("quote", quote_handler))
    app.add_handler(CommandHandler("info", info_handler))
    app.add_handler(CommandHandler("test_reminder", test_reminder_handler))

    # Register callback handlers (for inline keyboards)
    app.add_handler(CallbackQueryHandler(start_handler, pattern="^start_menu$"))
    app.add_handler(CallbackQueryHandler(start_handler, pattern="^page_"))
    app.add_handler(CallbackQueryHandler(province_callback_handler, pattern="^prov_"))

    # Register error handler
    app.add_error_handler(error_handler)

    # Start polling
    logger.info("🚀 Bot started! Listening for messages...")
    print("🕌 Bot Pengingat Sholat berjalan...")
    print("   Tekan Ctrl+C untuk menghentikan.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
