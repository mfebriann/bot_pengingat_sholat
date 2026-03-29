"""
Script to create the PostgreSQL database if it doesn't exist.
Run this ONCE before running seed_quotes.py.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse

db_url = os.getenv("DATABASE_URL", "")

parsed = urlparse(db_url)
dbname = parsed.path.lstrip("/")
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port or 5432

print(f"Connecting to PostgreSQL at {host}:{port} as '{user}'...")
print(f"Creating database '{dbname}'...")

try:
    # Connect to the default 'postgres' database to run CREATE DATABASE
    conn = psycopg2.connect(
        dbname="postgres",
        user=user,
        password=password,
        host=host,
        port=port,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if database already exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone()

    if exists:
        print(f"✅ Database '{dbname}' sudah ada.")
    else:
        cur.execute(f'CREATE DATABASE "{dbname}"')
        print(f"✅ Database '{dbname}' berhasil dibuat!")

    cur.close()
    conn.close()

except psycopg2.OperationalError as e:
    print(f"❌ Gagal konek ke PostgreSQL: {e}")
    print("\nPastikan:")
    print("  1. PostgreSQL sedang berjalan")
    print("  2. User, password, host, port di .env sudah benar")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
