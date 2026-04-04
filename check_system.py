import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from redis import Redis
from celery import Celery
import httpx

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings

def check_database():
    print("--- [1/4] Checking Database ---")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database Connection: SUCCESS")
    except Exception as e:
        print(f"❌ Database Connection: FAILED\n   Error: {e}")

def check_redis():
    print("\n--- [2/4] Checking Redis ---")
    try:
        redis = Redis.from_url(settings.REDIS_URL, socket_timeout=5)
        redis.ping()
        print("✅ Redis Connection: SUCCESS")
    except Exception as e:
        print(f"❌ Redis Connection: FAILED\n   Error: {e}")

def check_celery():
    print("\n--- [3/4] Checking Celery Workers ---")
    try:
        app = Celery('check', broker=settings.REDIS_URL)
        inspect = app.control.inspect()
        active = inspect.active()
        if active:
            print(f"✅ Celery Workers: ACTIVE ({len(active)} workers found)")
            for worker, tasks in active.items():
                print(f"   - {worker}: {len(tasks)} active tasks")
        else:
            print("⚠️ Celery Workers: NO ACTIVE WORKERS FOUND. Make sure 'celery worker' is running.")
    except Exception as e:
        print(f"❌ Celery Connection: FAILED\n   Error: {e}")

async def check_telegram():
    print("\n--- [4/4] Checking Telegram Connection ---")
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                bot_name = data.get('result', {}).get('first_name', 'Unknown')
                print(f"✅ Telegram API: SUCCESS (Bot: {bot_name})")
            else:
                print(f"❌ Telegram API: FAILED (Status {response.status_code})")
                print(f"   Response: {response.text}")
    except httpx.ReadError:
        print("❌ Telegram API: FAILED (ReadError - Network instability)")
    except Exception as e:
        print(f"❌ Telegram API: FAILED\n   Error: {e}")

if __name__ == "__main__":
    print("🔍 BOT PENGINGAT SHOLAT - SYSTEM DIAGNOSTICS\n")
    check_database()
    check_redis()
    check_celery()
    asyncio.run(check_telegram())
    print("\n--- Diagnostics Finished ---")
