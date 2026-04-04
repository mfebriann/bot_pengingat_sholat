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
            # Increased timeout to 20s for slow API responses
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                
                # Check for 502 Bad Gateway or 504 Gateway Timeout
                if response.status_code in [502, 504]:
                    logger.warning(
                        "Aladhan API returned %d for %s (attempt %d/%d). Retrying...",
                        response.status_code, city, attempt, MAX_RETRIES
                    )
                    if attempt < MAX_RETRIES:
                        import asyncio
                        await asyncio.sleep(2 * attempt)
                        continue

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
            # Retry on 5xx errors
            if attempt < MAX_RETRIES and e.response.status_code >= 500:
                import asyncio
                await asyncio.sleep(2 * attempt)
                continue
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching prayer times for %s (attempt %d/%d): %s",
                city, attempt, MAX_RETRIES, e,
            )
            # Retry on request errors (timeout, connection)
            if attempt < MAX_RETRIES:
                import asyncio
                await asyncio.sleep(2 * attempt)
                continue
        except (KeyError, ValueError) as e:
            logger.error(
                "Parse error for %s API response (attempt %d/%d): %s",
                city, attempt, MAX_RETRIES, e,
            )
            return None  # No point retrying a parse error

    logger.error("All %d retries failed for city %s", MAX_RETRIES, city)
    return None
