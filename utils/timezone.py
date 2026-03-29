"""
City-to-timezone mapping for Indonesian cities.

Indonesia has 3 time zones:
  - WIB  (Asia/Jakarta)   — Sumatera, Jawa, Kalimantan Barat & Tengah
  - WITA (Asia/Makassar)  — Kalimantan Timur & Selatan, Sulawesi, Bali, NTB, NTT
  - WIT  (Asia/Jayapura)  — Papua, Maluku
"""

from zoneinfo import ZoneInfo

# Grouping 38 provinces by region for Telegram Inline Keyboard
REGIONS = {
    "Sumatera": [
        "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau",
        "Jambi", "Sumatera Selatan", "Bengkulu", "Lampung", "Kepulauan Bangka Belitung"
    ],
    "Jawa": [
        "DKI Jakarta", "Jawa Barat", "Banten", "Jawa Tengah", "DI Yogyakarta", "Jawa Timur"
    ],
    "Bali & Nusa Tenggara": [
        "Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur"
    ],
    "Kalimantan": [
        "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara"
    ],
    "Sulawesi": [
        "Sulawesi Utara", "Gorontalo", "Sulawesi Tengah", "Sulawesi Barat", "Sulawesi Selatan", "Sulawesi Tenggara"
    ],
    "Maluku": [
        "Maluku", "Maluku Utara"
    ],
    "Papua": [
        "Papua", "Papua Barat", "Papua Tengah", "Papua Pegunungan", "Papua Selatan", "Papua Barat Daya"
    ]
}

# Mapping 38 provinces to Timezones
PROVINCE_TIMEZONE_MAP = {
    # WIB
    "Aceh": "Asia/Jakarta",
    "Sumatera Utara": "Asia/Jakarta",
    "Sumatera Barat": "Asia/Jakarta",
    "Riau": "Asia/Jakarta",
    "Kepulauan Riau": "Asia/Jakarta",
    "Jambi": "Asia/Jakarta",
    "Sumatera Selatan": "Asia/Jakarta",
    "Bengkulu": "Asia/Jakarta",
    "Lampung": "Asia/Jakarta",
    "Kepulauan Bangka Belitung": "Asia/Jakarta",
    "DKI Jakarta": "Asia/Jakarta",
    "Jawa Barat": "Asia/Jakarta",
    "Banten": "Asia/Jakarta",
    "Jawa Tengah": "Asia/Jakarta",
    "DI Yogyakarta": "Asia/Jakarta",
    "Jawa Timur": "Asia/Jakarta",
    "Kalimantan Barat": "Asia/Jakarta",
    "Kalimantan Tengah": "Asia/Jakarta",

    # WITA
    "Bali": "Asia/Makassar",
    "Nusa Tenggara Barat": "Asia/Makassar",
    "Nusa Tenggara Timur": "Asia/Makassar",
    "Kalimantan Selatan": "Asia/Makassar",
    "Kalimantan Timur": "Asia/Makassar",
    "Kalimantan Utara": "Asia/Makassar",
    "Sulawesi Utara": "Asia/Makassar",
    "Gorontalo": "Asia/Makassar",
    "Sulawesi Tengah": "Asia/Makassar",
    "Sulawesi Barat": "Asia/Makassar",
    "Sulawesi Selatan": "Asia/Makassar",
    "Sulawesi Tenggara": "Asia/Makassar",

    # WIT
    "Maluku": "Asia/Jayapura",
    "Maluku Utara": "Asia/Jayapura",
    "Papua": "Asia/Jayapura",
    "Papua Barat": "Asia/Jayapura",
    "Papua Tengah": "Asia/Jayapura",
    "Papua Pegunungan": "Asia/Jayapura",
    "Papua Selatan": "Asia/Jayapura",
    "Papua Barat Daya": "Asia/Jayapura"
}


def get_timezone(province: str) -> ZoneInfo | None:
    normalized = province.strip().title()
    # Handle specific title casing exceptions if needed (e.g. DKI Jakarta)
    tz_str = get_timezone_str(province)
    return ZoneInfo(tz_str) if tz_str else None


def get_timezone_str(province: str) -> str | None:
    # Do case-insensitive match loop to handle exact capitalizations
    lookup = province.strip().lower()
    for prov_name, tz_str in PROVINCE_TIMEZONE_MAP.items():
        if prov_name.lower() == lookup:
            return tz_str
    return None


def get_timezone_label(tz_str: str) -> str:
    labels = {
        "Asia/Jakarta": "WIB",
        "Asia/Makassar": "WITA",
        "Asia/Jayapura": "WIT",
    }
    return labels.get(tz_str, "WIB")


def get_all_registered_cities(session) -> list[str]:
    from models.user import User
    result = session.query(User.city).distinct().filter(User.city.isnot(None)).all()
    return [row[0] for row in result]
