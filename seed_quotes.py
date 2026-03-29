"""
Seed script — populate the quotes table with Islamic quotes.

Usage:
    python seed_quotes.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.base import SessionLocal, init_db
from models.quote import Quote
from utils.logger import setup_logger

logger = setup_logger("seed_quotes")

QUOTES = [
    # ─── Ayat Al-Quran (Umum) ─────────────────────────────────────────────
    {
        "type": "quran",
        "content": "Sesungguhnya sholat itu mencegah dari perbuatan keji dan mungkar.",
        "source": "Al-Quran",
        "surah_name": "Al-Ankabut",
        "surah_number": 29,
        "ayah_number": 45,
        "prayer_time": None,
    },
    {
        "type": "quran",
        "content": "Peliharalah semua sholat dan sholat wustha (Ashar). Dan berdirilah karena Allah dengan khusyuk.",
        "source": "Al-Quran",
        "surah_name": "Al-Baqarah",
        "surah_number": 2,
        "ayah_number": 238,
        "prayer_time": "asr",
    },
    {
        "type": "quran",
        "content": "Sesungguhnya sholat itu adalah kewajiban yang ditentukan waktunya atas orang-orang yang beriman.",
        "source": "Al-Quran",
        "surah_name": "An-Nisa",
        "surah_number": 4,
        "ayah_number": 103,
        "prayer_time": None,
    },
    {
        "type": "quran",
        "content": "Dan dirikanlah sholat, tunaikanlah zakat, dan rukuklah beserta orang-orang yang rukuk.",
        "source": "Al-Quran",
        "surah_name": "Al-Baqarah",
        "surah_number": 2,
        "ayah_number": 43,
        "prayer_time": None,
    },
    {
        "type": "quran",
        "content": "Maka bertasbihlah kepada Allah pada petang dan pagi hari.",
        "source": "Al-Quran",
        "surah_name": "Ar-Rum",
        "surah_number": 30,
        "ayah_number": 17,
        "prayer_time": None,
    },
    # ─── Ayat Al-Quran (Subuh) ───────────────────────────────────────────
    {
        "type": "quran",
        "content": "Dirikanlah sholat dari sesudah matahari tergelincir sampai gelap malam dan (dirikanlah pula sholat) Subuh.",
        "source": "Al-Quran",
        "surah_name": "Al-Isra",
        "surah_number": 17,
        "ayah_number": 78,
        "prayer_time": "fajr",
    },
    {
        "type": "quran",
        "content": "Dan bertasbihlah dengan memuji Tuhanmu sebelum terbit matahari (Subuh).",
        "source": "Al-Quran",
        "surah_name": "Qaf",
        "surah_number": 50,
        "ayah_number": 39,
        "prayer_time": "fajr",
    },

    # ─── Hadits (Umum) ───────────────────────────────────────────────────
    {
        "type": "hadith",
        "content": "Sholat adalah tiang agama. Barangsiapa yang mendirikannya, maka ia telah menegakkan agama.",
        "source": "HR. Baihaqi",
        "prayer_time": None,
    },
    {
        "type": "hadith",
        "content": "Amalan yang pertama kali dihisab dari seorang hamba pada hari kiamat adalah sholatnya.",
        "source": "HR. Abu Dawud & Tirmidzi",
        "prayer_time": None,
    },
    {
        "type": "hadith",
        "content": "Sholat adalah cahaya bagi orang beriman.",
        "source": "HR. Muslim",
        "prayer_time": None,
    },
    
    # ─── Hadits (Subuh) ──────────────────────────────────────────────────
    {
        "type": "hadith",
        "content": "Dua rakaat Subuh (sholat sunnah Subuh) lebih baik daripada dunia dan seisinya.",
        "source": "HR. Muslim",
        "prayer_time": "fajr",
    },
    {
        "type": "hadith",
        "content": "Seseorang yang sholat Subuh berjamaah, maka ia berada dalam jaminan Allah.",
        "source": "HR. Muslim",
        "prayer_time": "fajr",
    },
    {
        "type": "hadith",
        "content": "Malaikat malam dan malaikat siang berkumpul pada waktu sholat Subuh.",
        "source": "HR. Bukhari",
        "prayer_time": "fajr",
    },

    # ─── Hadits (Ashar) ──────────────────────────────────────────────────
    {
        "type": "hadith",
        "content": "Barangsiapa yang meninggalkan sholat Ashar, maka terhapuslah amalannya.",
        "source": "HR. Bukhari",
        "prayer_time": "asr",
    },
    {
        "type": "hadith",
        "content": "Seseorang tidak akan masuk neraka bagi yang melaksanakan sholat sebelum matahari terbit (Subuh) dan sebelum matahari terbenam (Ashar).",
        "source": "HR. Muslim",
        "prayer_time": "asr",  # Relevant to both, but putting in ashr
    },

    # ─── Nasihat (Umum) ──────────────────────────────────────────────────
    {
        "type": "wisdom",
        "content": "Ketika kamu merasa berat untuk sholat, itulah saat kamu paling membutuhkannya.",
        "source": "Nasihat Ulama",
        "prayer_time": None,
    },
    {
        "type": "wisdom",
        "content": "Sholatlah agar hatimu tenang, karena ketenangan hanya milik Allah.",
        "source": "Nasihat Bijak",
        "prayer_time": None,
    },
    {
        "type": "wisdom",
        "content": "Jangan biarkan dunia menghalangimu dari sholat tepat waktu.",
        "source": "Nasihat Islami",
        "prayer_time": None,
    },
]

def seed():
    """Insert quotes into the database."""
    from models.base import engine
    
    print("Recreating quotes table...")
    Quote.__table__.drop(bind=engine, checkfirst=True)
    init_db()
    
    session = SessionLocal()

    try:
        for q in QUOTES:
            quote = Quote(**q)
            session.add(quote)

        session.commit()
        count = session.query(Quote).count()
        print(f"Berhasil menambahkan {count} quotes ke database.")
        logger.info("Seeded %d quotes", count)

    except Exception as e:
        session.rollback()
        logger.error("Seed error: %s", e)
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed()
