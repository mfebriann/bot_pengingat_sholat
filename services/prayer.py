"""
Prayer time service — orchestrates cache and API to return prayer times.
Provides a random Islamic quote from the database.
"""

import asyncio
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.base import SessionLocal
from models.quote import Quote
from services.aladhan import fetch_prayer_times
from services.cache import get_cached_prayer_times, set_cached_prayer_times
from utils.logger import setup_logger

logger = setup_logger("services.prayer")


async def get_prayer_times(city: str, date_str: str | None = None) -> dict[str, str] | None:
    """
    Get prayer times for a city — cache first, fallback to API.

    Args:
        city: City name.
        date_str: Date in YYYY-MM-DD format. Defaults to today.

    Returns:
        Dict of prayer times or None on failure.
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Try cache
    cached = get_cached_prayer_times(city, date_str)
    if cached:
        logger.info("Returning cached prayer times for %s on %s", city, date_str)
        return cached

    # 2. Cache miss — fetch from API
    logger.info("Cache miss for %s on %s, fetching from API...", city, date_str)

    # Aladhan API expects DD-MM-YYYY
    parts = date_str.split("-")
    api_date = f"{parts[2]}-{parts[1]}-{parts[0]}" if len(parts) == 3 else None

    times = await fetch_prayer_times(city, api_date)
    if times is None:
        logger.error("Failed to fetch prayer times for %s", city)
        return None

    # 3. Cache the result
    set_cached_prayer_times(city, date_str, times)

    return times


def get_prayer_times_sync(city: str, date_str: str | None = None) -> dict[str, str] | None:
    """
    Synchronous wrapper for get_prayer_times (used by Celery workers).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, create a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run, get_prayer_times(city, date_str)
                ).result()
            return result
        else:
            return loop.run_until_complete(get_prayer_times(city, date_str))
    except RuntimeError:
        return asyncio.run(get_prayer_times(city, date_str))


def get_random_quote(prayer_name: str | None = None) -> Quote | None:
    """
    Get a random Islamic quote from the database.
    Can filter by prayer_name (e.g. 'Subuh', 'Ashar').

    Args:
        prayer_name: Optional name of the prayer time.

    Returns:
        A Quote object or None if no quotes exist.
    """
    session: Session = SessionLocal()
    from sqlalchemy import or_
    try:
        query = session.query(Quote)
        if prayer_name:
            # Normalize for matching ('Subuh' -> 'subuh')
            p_name = prayer_name.lower().strip()
            # Select quotes matching THIS prayer_time OR general quotes (NULL)
            query = query.filter(or_(Quote.prayer_time == p_name, Quote.prayer_time == None))

        quote = query.order_by(func.random()).first()
        if quote:
            # Eagerly load all attributes before closing session
            _ = quote.content, quote.source, quote.type
            _ = quote.surah_name, quote.surah_number, quote.ayah_number
            _ = quote.prayer_time
        return quote
    except Exception as e:
        logger.error("Error fetching random quote: %s", e)
        return None
    finally:
        session.close()
