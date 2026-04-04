"""
Celery tasks for prayer time reminders.

Tasks:
  - send_reminder: Send a prayer reminder to all users in a city.
  - schedule_city_reminders: Schedule H-10 and on-time reminders for a city.
  - refresh_all_schedules: Daily task to refresh all registered cities.
"""

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from workers.celery_app import celery_app
from config.settings import settings
from models.base import SessionLocal
from models.user import User
from services.prayer import get_prayer_times_sync, get_random_quote
from services.cache import acquire_lock, release_lock
from utils.timezone import get_timezone_str, get_timezone_label, get_all_registered_cities
from utils.logger import setup_logger

logger = setup_logger("workers.tasks")


import time


def _send_telegram_message(chat_id: int, text: str, max_retries: int = 3) -> bool:
    """
    Send a message via Telegram Bot API with retries and exponential backoff.

    Returns True if sent successfully.
    """
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            # Use httpx.post directly (sync)
            response = httpx.post(url, json=payload, timeout=20.0)
            
            # Special case: 429 Too Many Requests (Rate limit)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                logger.warning("Rate limited by Telegram. Waiting %ds (Attempt %d/%d)", retry_after, attempt, max_retries)
                time.sleep(retry_after)
                continue
                
            response.raise_for_status()
            logger.info("Message sent to chat_id=%s", chat_id)
            return True
            
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            # Check if it's a 4xx error that won't succeed after retry (e.g., bot blocked)
            if isinstance(e, httpx.HTTPStatusError):
                status_code = e.response.status_code
                # 403 Forbidden: Bot blocked by user OR 400 Bad Request: Chat not found
                if 400 <= status_code < 500 and status_code != 429:
                    logger.error("Permanent failure sending to chat_id=%s (Status %d): %s", chat_id, status_code, e)
                    return False
            
            # Retry for network errors (ReadError, ConnectionError) or 5xx (Bad Gateway, etc.)
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 2, 4, 8s backoff
                logger.warning(
                    "Attempt %d/%d failed for chat_id=%s: %s. Retrying in %ds...", 
                    attempt, max_retries, chat_id, e, wait_time
                )
                time.sleep(wait_time)
            else:
                logger.error("All %d retries failed for chat_id=%s: %s", max_retries, chat_id, e)
                
    return False



def _get_users_by_city(city: str) -> list[int]:
    """Get all telegram_ids of users registered in a city."""
    session = SessionLocal()
    try:
        users = (
            session.query(User.telegram_id)
            .filter(User.city == city.strip().title())
            .all()
        )
        return [u.telegram_id for u in users]
    finally:
        session.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="workers.tasks.send_reminder",
)
def send_reminder(self, city: str, prayer_name: str, prayer_time: str, reminder_type: str):
    """
    Send a prayer time reminder to all users in a given city.

    Args:
        city: City name (title-cased).
        prayer_name: Prayer name (e.g. 'Maghrib').
        prayer_time: Time string (e.g. '18:05').
        reminder_type: 'before' or 'ontime'.
    """
    display_name = settings.PRAYER_DISPLAY_NAMES.get(prayer_name, prayer_name)
    tz_str = get_timezone_str(city)
    tz_label = get_timezone_label(tz_str) if tz_str else "WIB"

    if reminder_type == "before":
        message = (
            f"⏳ <b>10 menit lagi</b> waktu sholat <b>{display_name}</b> "
            f"di <b>{city}</b>.\n\n"
            f"🕐 Pukul {prayer_time} {tz_label}\n\n"
            f"Bersiap-siaplah untuk menunaikan sholat. 🤲"
        )
    else:
        # On-time reminder with random quote
        from services.prayer import get_random_prayer_quote

        quote = get_random_prayer_quote(prayer_name)
        quote_text = ""
        if quote:
            quote_text = f"\n\n📖 <i>{quote.content}</i>"
            if quote.source:
                quote_text += f"\n— <b>{quote.source}</b>"
            if quote.surah_name and quote.ayah_number:
                quote_text += f" (QS. {quote.surah_name}: {quote.ayah_number})"

        message = (
            f"🕌 <b>Waktu Sholat {display_name}</b>\n\n"
            f"📍 Provinsi: <b>{city}</b>\n"
            f"🕐 Waktu: <b>{prayer_time} {tz_label}</b>\n\n"
            f"Saatnya menunaikan sholat <b>{display_name}</b>. "
            f"Semoga Allah senantiasa menerima ibadah kita. 🤲"
            f"{quote_text}"
        )

    # Send to all users in this city
    telegram_ids = _get_users_by_city(city)
    if not telegram_ids:
        logger.warning("No users registered in %s, skipping reminder", city)
        return

    success_count = 0
    fail_count = 0
    for tid in telegram_ids:
        if _send_telegram_message(tid, message):
            success_count += 1
        else:
            fail_count += 1

    logger.info(
        "Reminder [%s] %s at %s in %s — sent: %d, failed: %d",
        reminder_type, display_name, prayer_time, city,
        success_count, fail_count,
    )

    # Retry if all failed
    if success_count == 0 and fail_count > 0:
        try:
            self.retry(exc=Exception(f"All sends failed for {city}"))
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for reminder in %s", city)


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    name="workers.tasks.schedule_city_reminders",
)
def schedule_city_reminders(self, city: str):
    """
    Schedule H-10 and on-time reminders for all prayers in a city for today.

    Uses a Redis lock to prevent duplicate scheduling.
    """
    tz_str = get_timezone_str(city)
    if not tz_str:
        logger.error("Unknown timezone for city %s", city)
        return

    tz = ZoneInfo(tz_str)
    today = datetime.now(tz)
    date_str = today.strftime("%Y-%m-%d")

    lock_name = f"schedule:{city.lower()}:{date_str}"
    lock = acquire_lock(lock_name, timeout=600)
    if not lock:
        logger.info("Schedule already running for %s on %s, skipping", city, date_str)
        return

    try:
        # Fetch prayer times (sync wrapper)
        times = get_prayer_times_sync(city, date_str)
        if not times:
            logger.error("Could not get prayer times for %s on %s", city, date_str)
            try:
                self.retry(exc=Exception(f"No prayer times for {city}"))
            except self.MaxRetriesExceededError:
                logger.error("Max retries exceeded for scheduling %s", city)
            return

        now = datetime.now(tz)

        for prayer_name, time_str in times.items():
            try:
                hour, minute = map(int, time_str.split(":"))
                prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                # Schedule on-time reminder
                if prayer_dt > now:
                    delay_seconds = (prayer_dt - now).total_seconds()
                    send_reminder.apply_async(
                        args=[city, prayer_name, time_str, "ontime"],
                        countdown=delay_seconds,
                    )
                    logger.info(
                        "Scheduled ON-TIME reminder for %s %s at %s (in %.0fs)",
                        city, prayer_name, time_str, delay_seconds,
                    )

                # Schedule H-10 reminder
                before_dt = prayer_dt - timedelta(minutes=settings.REMINDER_BEFORE_MINUTES)
                if before_dt > now:
                    delay_before = (before_dt - now).total_seconds()
                    send_reminder.apply_async(
                        args=[city, prayer_name, time_str, "before"],
                        countdown=delay_before,
                    )
                    logger.info(
                        "Scheduled H-10 reminder for %s %s at %s (in %.0fs)",
                        city, prayer_name, time_str, delay_before,
                    )

            except (ValueError, TypeError) as e:
                logger.error(
                    "Error scheduling %s for %s: %s", prayer_name, city, e
                )

        logger.info("All reminders scheduled for %s on %s", city, date_str)

    finally:
        release_lock(lock)


@celery_app.task(name="workers.tasks.refresh_all_schedules")
def refresh_all_schedules():
    """
    Daily task: refresh prayer times and schedule reminders for all registered cities.

    Called by Celery Beat at 00:05 every day.
    """
    session = SessionLocal()
    try:
        cities = get_all_registered_cities(session)
    finally:
        session.close()

    if not cities:
        logger.info("No cities registered, nothing to refresh")
        return

    logger.info("Refreshing schedules for %d cities: %s", len(cities), cities)

    for city in cities:
        schedule_city_reminders.delay(city)

    logger.info("All city schedule tasks dispatched")
