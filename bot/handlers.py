"""
Telegram bot command handlers.
"""

from datetime import datetime
import math
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.base import SessionLocal
from models.user import User
from services.prayer import get_prayer_times, get_random_islamic_quote, get_random_prayer_quote
from utils.timezone import (
    get_timezone,
    get_timezone_str,
    get_timezone_label,
    PROVINCE_TIMEZONE_MAP,
)
from utils.quote_image import generate_quote_image_jpeg
from utils.logger import setup_logger
from config.settings import settings
import kombu.exceptions
import redis.exceptions

# Trigger city scheduling after /setcity (now /start callback)
from workers.tasks import schedule_city_reminders

logger = setup_logger("bot.handlers")


# ─── /start & Location Selection ──────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command — welcome message & location selection."""
    user = update.effective_user
    
    page = 0
    if update.callback_query and update.callback_query.data.startswith("page_"):
        page = int(update.callback_query.data.split("_")[1])

    provinces = sorted(PROVINCE_TIMEZONE_MAP.keys())
    ITEMS_PER_PAGE = 20
    
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_provinces = provinces[start_idx:end_idx]
    
    keyboard = []
    # Create 2 columns for provinces, sorted A-Z
    for i in range(0, len(current_provinces), 2):
        row = []
        for prov in current_provinces[i:i+2]:
            row.append(InlineKeyboardButton(prov, callback_data=f"prov_{prov}"))
        keyboard.append(row)
        
    # Navigation Buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data=f"page_{page-1}"))
    if end_idx < len(provinces):
        nav_row.append(InlineKeyboardButton("Selanjutnya ➡️", callback_data=f"page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome = (
        f"Assalamu'alaikum, {user.first_name}! 👋\n\n"
        "🕌 Selamat datang di <b>Bot Pengingat Sholat</b>.\n\n"
        "Silakan pilih <b>Provinsi</b> Anda untuk mulai mengonfigurasi lokasi pengingat sholat:"
    )
    
    if update.callback_query:
        await update.callback_query.message.edit_text(welcome, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode="HTML")
    if not update.callback_query:
        logger.info("User %s (%s) started the bot", user.id, user.first_name)


async def province_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle province selection and save to database."""
    query = update.callback_query
    await query.answer()

    province_input = query.data.split("_")[1]
    tz_str = get_timezone_str(province_input)
    
    if not tz_str:
        await query.message.reply_text("❌ Provinsi tidak valid.")
        return

    tz_label = get_timezone_label(tz_str)
    telegram_id = update.effective_user.id

    # Save to database
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.city = province_input  # using the existing 'city' column
            user.timezone = tz_str
        else:
            user = User(
                telegram_id=telegram_id,
                city=province_input,
                timezone=tz_str,
            )
            session.add(user)
        session.commit()

        await query.message.edit_text(
            f"✅ Lokasi berhasil di-set!\n\n"
            f"📍 Provinsi: <b>{province_input}</b>\n"
            f"🕐 Zona Waktu: <b>{tz_label}</b> ({tz_str})\n\n"
            f"Kamu akan menerima pengingat sholat.\n"
            f"Ketik /jadwal untuk melihat jadwal hari ini.",
            parse_mode="HTML",
        )
        logger.info("User %s set province to %s (%s)", telegram_id, province_input, tz_label)

        # Trigger scheduling for this province, gracefully handling missing Redis
        # Wrap Celery delay in thread to prevent blocking asyncio loop if Redis hangs
        try:
            def sync_celery_call():
                schedule_city_reminders.delay(province_input)
            await asyncio.to_thread(sync_celery_call)
            logger.info("Triggered schedule_city_reminders for %s", province_input)
        except Exception as e:
            logger.error("Failed to trigger Celery schedule (Redis might be offline): %s", e)
            await context.bot.send_message(
                chat_id=telegram_id, 
                text="⚠️ <i>Peringatan Sistem: Service scheduler gagal dijangkau (Redis Offline). /jadwal tetap siap.</i>", 
                parse_mode="HTML"
            )

    except Exception as e:
        session.rollback()
        logger.error("Database error in set province for user %s: %s", telegram_id, e)
        await query.message.reply_text(
            "❌ Terjadi kesalahan saat menyimpan lokasi. Silakan coba lagi.",
        )
    finally:
        session.close()

# ─── Commands ─────────────────────────────────────────────────────────────────


# ─── /jadwal ──────────────────────────────────────────────────────────────────

async def jadwal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /jadwal command — show today's prayer times."""
    telegram_id = update.effective_user.id

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
    finally:
        session.close()

    if not user or not user.city:
        await update.message.reply_text(
            "⚠️ Kamu belum set provinsi.\n\n"
            "Silakan set provinsi terlebih dahulu:\n"
            "Ketik /start lalu pilih provinsi.",
        )
        return

    city = user.city
    tz_str = user.timezone or get_timezone_str(city) or "Asia/Jakarta"
    tz_label = get_timezone_label(tz_str)

    # Send "loading" message
    loading_msg = await update.message.reply_text("⏳ Mengambil jadwal sholat...")

    try:
        times = await get_prayer_times(city)
    except Exception as e:
        logger.error("Error getting prayer times for %s: %s", city, e)
        await loading_msg.edit_text(
            "❌ Gagal mengambil jadwal sholat. Silakan coba lagi nanti."
        )
        return

    if not times:
        await loading_msg.edit_text(
            f"❌ Tidak dapat mengambil jadwal sholat untuk <b>{city}</b>.\n"
            "Silakan coba lagi nanti.",
            parse_mode="HTML",
        )
        return

    # Format the schedule
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    
    now = datetime.now()
    day_name = days[now.weekday()]
    month_name = months[now.month - 1]
    today_indo = f"{day_name}, {now.day} {month_name} {now.year}"

    lines = [
        f"🕌 <b>Jadwal Sholat — {city}</b>",
        f"🗓 {today_indo}",
        f"🕐 Zona Waktu: {tz_label}\n",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]

    prayer_emojis = {
        "Fajr": "🌅",
        "Dhuhr": "☀️",
        "Asr": "🌤️",
        "Maghrib": "🌇",
        "Isha": "🌙",
    }

    for prayer_name in settings.PRAYER_NAMES:
        time_str = times.get(prayer_name, "-")
        display_name = settings.PRAYER_DISPLAY_NAMES.get(prayer_name, prayer_name)
        emoji = prayer_emojis.get(prayer_name, "🕐")
        lines.append(f"  {emoji}  <b>{display_name}</b>   →   {time_str} {tz_label}")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("\n🔔 Reminder otomatis aktif (H-10 menit)")

    await loading_msg.edit_text("\n".join(lines), parse_mode="HTML")
    logger.info("Showed jadwal for user %s in %s", telegram_id, city)


# ─── /info ────────────────────────────────────────────────────────────────────

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command — list available commands."""
    help_text = (
        "📋 <b>Daftar Perintah</b>\n\n"
        "🔹 /start — Mulai bot & Set Lokasi (Provinsi)\n"
        "🔹 /jadwal — Lihat jadwal sholat hari ini\n"
        "🔹 /info — Lihat info lokasi & timezone kamu\n"
        "🔹 /quote — Quote islami (gambar)\n"
        "🔹 /feedback — Masukkan & saran\n"
        "🔹 /help — Tampilkan bantuan ini\n\n"
        "💡 <b>Tips:</b>\n"
        "• Bot akan mengirimkan pengingat H-10 menit otomatis\n"
        "• Jadwal ini mencakup seluruh provinsi di Indonesia"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /feedback command — how to send suggestions."""
    message = update.effective_message
    if message is None:
        return

    await message.reply_text(
        "💬 <b>Feedback / Masukkan</b>\n\n"
        "Punya masukkan atau saran? Silakan hubungi:\n"
        "@riann18",
        parse_mode="HTML",
    )


async def quote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /quote command — send a random Islamic quote as an image."""
    message = update.effective_message
    if message is None:
        return

    loading_msg = await message.reply_text("⏳ Sedang menyiapkan quote...")

    quote = get_random_islamic_quote()
    if not quote:
        await loading_msg.edit_text(
            "⚠️ Quote belum tersedia. Jalankan `python seed_quotes.py` untuk mengisi database."
        )
        return

    source_text: str | None = quote.source.strip() if quote.source else None
    if quote.surah_name and quote.ayah_number:
        qs = f"QS. {quote.surah_name}: {quote.ayah_number}"
        source_text = f"{source_text} ({qs})" if source_text else qs

    try:
        image_bytes = generate_quote_image_jpeg(quote.content, source_text=source_text)
        image_bytes.name = "quote.jpg"
    except Exception as e:
        await loading_msg.edit_text(f"❌ Gagal membuat gambar quote: {e}")
        return

    await message.reply_photo(photo=image_bytes)
    try:
        await loading_msg.delete()
    except Exception:
        await loading_msg.edit_text("✅ Quote siap.")


async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /info command — show user's current settings."""
    telegram_id = update.effective_user.id

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
    finally:
        session.close()

    if not user or not user.city:
        await update.message.reply_text(
            "⚠️ Kamu belum set provinsi.\n\n"
            "Silakan set provinsi terlebih dahulu:\n"
            "Ketik /start lalu pilih provinsi.",
        )
        return

    tz_label = get_timezone_label(user.timezone or "Asia/Jakarta")
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    if user.created_at:
        m_name = months[user.created_at.month - 1]
        registered_at = f"{user.created_at.day} {m_name} {user.created_at.year}"
    else:
        registered_at = "-"

    info_text = (
        "ℹ️ <b>Info Akun Kamu</b>\n\n"
        f"📍 Provinsi: <b>{user.city}</b>\n"
        f"🕐 Zona Waktu: <b>{tz_label}</b> ({user.timezone})\n"
        f"🗓 Terdaftar: {registered_at}\n\n"
        ""
    )
    await update.message.reply_text(info_text, parse_mode="HTML")


# ─── /test_reminder ───────────────────────────────────────────────────────────

async def test_reminder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /test_reminder command — send simulated reminders (Admin only)."""
    telegram_id = update.effective_user.id
    
    if telegram_id != settings.ADMIN_ID:
        await update.message.reply_text("⛔ Perintah ini hanya untuk Admin.")
        return
        
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
    finally:
        session.close()

    if not user or not user.city:
        await update.message.reply_text("⚠️ Silakan set provinsi terlebih dahulu (ketik /start) untuk simulasi Anda.")
        return

    city = user.city
    tz_label = get_timezone_label(user.timezone or "Asia/Jakarta")
    prayer_name = "Maghrib"
    display_name = settings.PRAYER_DISPLAY_NAMES.get(prayer_name, prayer_name)
    prayer_time = "18:00"

    # 1. Test H-10 Reminder
    msg_before = (
        f"⏳ <b>10 menit lagi</b> waktu sholat <b>{display_name}</b> "
        f"di <b>{city}</b>.\n\n"
        f"🕐 Pukul {prayer_time} {tz_label}\n\n"
        f"Bersiap-siaplah untuk menunaikan sholat. 🤲"
    )
    await update.message.reply_text(f"🛠️ <b>TESTING: Pengingat H-10 Menit</b>\n\n{msg_before}", parse_mode="HTML")

    # 2. Test On-Time Reminder
    quote = get_random_prayer_quote(prayer_name)
    quote_text = ""
    if quote:
        quote_text = f"\n\n📖 <i>{quote.content}</i>"
        if quote.source:
            quote_text += f"\n— <b>{quote.source}</b>"
        if quote.surah_name and quote.ayah_number:
            quote_text += f" (QS. {quote.surah_name}: {quote.ayah_number})"

    msg_ontime = (
        f"🕌 <b>Waktu Sholat {display_name}</b>\n\n"
        f"📍 Provinsi: <b>{city}</b>\n"
        f"🕐 Waktu: <b>{prayer_time} {tz_label}</b>\n\n"
        f"Saatnya menunaikan sholat <b>{display_name}</b>. "
        f"Semoga Allah senantiasa menerima ibadah kita. 🤲"
        f"{quote_text}"
    )
    await update.message.reply_text(f"🛠️ <b>TESTING: Pengingat Tepat Waktu</b>\n\n{msg_ontime}", parse_mode="HTML")


# ─── Error handler ────────────────────────────────────────────────────────────

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors from the bot dispatcher."""
    logger.error("Update %s caused error: %s", update, context.error)
