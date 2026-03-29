"""
One-off migration: add Quote.category column to the `quotes` table.

Repo ini belum memakai Alembic. Script ini aman dijalankan berulang (idempotent)
untuk memastikan kolom `quotes.category` ada di database lama.

Usage:
    python migrate_add_quote_category.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from sqlalchemy import text

from models.base import engine
from utils.logger import setup_logger

logger = setup_logger("migrate_add_quote_category")


def main() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE quotes "
                "ADD COLUMN IF NOT EXISTS category VARCHAR(30) NOT NULL DEFAULT 'general'"
            )
        )
        # Dataset lama di repo ini mayoritas terkait sholat; tandai sebagai "prayer".
        conn.execute(text("UPDATE quotes SET category = 'prayer' WHERE category = 'general'"))

    logger.info("Migration complete: quotes.category ensured.")
    print("✅ Migration complete: `quotes.category` ensured.")


if __name__ == "__main__":
    main()

