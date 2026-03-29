"""
Aladhan API client for fetching prayer times.
"""

import httpx
from typing import Any

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger("services.aladhan")

# Maximum retries for API calls
MAX_RETRIES = 3


async def fetch_prayer_times(city: str, date: str | None = None) -> dict[str, str] | None:
    """
    Fetch prayer times from the Aladhan API for a given Indonesian city.

    Args:
        city: City name (e.g. 'Jakarta').
        date: Optional date string in DD-MM-YYYY format. If None, returns today's times.

    Returns:
        Dict with prayer names as keys and time strings (HH:MM) as values,
        or None on failure.
    """
    url = f"{settings.ALADHAN_BASE_URL}/timingsByCity"
    params: dict[str, Any] = {
        "city": city,
        "country": "Indonesia",
    }
    if date:
        params["date"] = date

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

            data = response.json()

            if data.get("code") != 200:
                logger.warning(
                    "Aladhan API returned non-200 code for %s: %s",
                    city,
                    data.get("status"),
                )
                return None

            timings = data["data"]["timings"]

            # Extract only the 5 daily prayers
            prayer_times: dict[str, str] = {}
            for prayer in settings.PRAYER_NAMES:
                raw_time = timings.get(prayer, "")
                # Remove timezone offset if present (e.g. "05:00 (WIB)")
                clean_time = raw_time.split(" ")[0] if raw_time else ""
                prayer_times[prayer] = clean_time

            logger.info("Fetched prayer times for %s: %s", city, prayer_times)
            return prayer_times

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching prayer times for %s (attempt %d/%d): %s",
                city, attempt, MAX_RETRIES, e,
            )
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching prayer times for %s (attempt %d/%d): %s",
                city, attempt, MAX_RETRIES, e,
            )
        except (KeyError, ValueError) as e:
            logger.error(
                "Parse error for %s API response (attempt %d/%d): %s",
                city, attempt, MAX_RETRIES, e,
            )
            return None  # No point retrying a parse error

    logger.error("All %d retries failed for city %s", MAX_RETRIES, city)
    return None
