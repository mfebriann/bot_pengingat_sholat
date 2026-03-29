# 🕌 Bot Pengingat Sholat Indonesia

Bot Telegram pengingat waktu sholat 5 waktu untuk kota-kota di Indonesia. Menggunakan data dari [Aladhan API](https://aladhan.com/prayer-times-api).

## ⚙️ Tech Stack

| Teknologi | Fungsi |
|-----------|--------|
| Python 3.10+ | Bahasa utama |
| python-telegram-bot | Telegram Bot API (async) |
| PostgreSQL | Database (users, quotes) |
| Redis | Cache, message broker, distributed lock |
| Celery | Task queue & worker |
| Celery Beat | Scheduler harian |
| httpx | HTTP client (Aladhan API) |
| SQLAlchemy | ORM |

## 📁 Struktur Project

```
├── bot/
│   ├── handlers.py      # Command handlers (/start, /setcity, /jadwal, /help, /info)
│   └── main.py          # Entry point bot
├── config/
│   └── settings.py      # Environment config
├── models/
│   ├── base.py          # SQLAlchemy base, engine, session
│   ├── user.py          # Model User
│   └── quote.py         # Model Quote
├── services/
│   ├── aladhan.py       # Aladhan API client
│   ├── cache.py         # Redis cache layer
│   └── prayer.py        # Prayer times service (cache + API)
├── workers/
│   ├── celery_app.py    # Celery configuration
│   ├── tasks.py         # Celery tasks (reminders, scheduling)
│   └── beat_schedule.py # Periodic task schedule
├── utils/
│   ├── timezone.py      # City → timezone mapping
│   └── logger.py        # Logging configuration
├── logs/                # Log files
├── seed_quotes.py       # Seed Islamic quotes ke DB
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Setup & Instalasi

### 1. Prerequisites

Pastikan sudah terinstall:
- **Python 3.10+**
- **PostgreSQL** (running)
- **Redis** (running) - *Untuk pengguna Windows, Anda bisa download [Redis for Windows by tporadowski (.msi)](https://github.com/tporadowski/redis/releases), lalu install/jalankan `redis-server.exe`.*

### 2. Clone & Virtual Environment

```bash
# Masuk ke folder project
cd "d:\Rian-Folder\Bot\Pengingat Sholat"

# Buat virtual environment
python -m venv venv

# Aktivasi venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment

```bash
# Copy template .env
copy .env.example .env

# Edit .env dan isi:
# - TELEGRAM_BOT_TOKEN  → dari @BotFather
# - DATABASE_URL        → PostgreSQL connection string
# - REDIS_URL           → Redis connection string
```

Contoh `.env`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=postgresql://postgres:password@localhost:5432/prayer_bot
REDIS_URL=redis://localhost:6379/0
```

### 5. Buat Database

```sql
-- Di PostgreSQL
CREATE DATABASE prayer_bot;
```

### 6. Seed Quotes

```bash
python seed_quotes.py
```

## ▶️ Menjalankan

### 1. Start Bot (Terminal 1)

```bash
python bot/main.py
```

### 2. Start Celery Worker (Terminal 2)

```bash
celery -A workers.celery_app worker --loglevel=info --pool=solo
```

> **Note Windows**: Gunakan `--pool=solo` karena Celery di Windows tidak support prefork.

### 3. Start Celery Beat (Terminal 3)

```bash
celery -A workers.celery_app beat --loglevel=info
```

### Contoh Penggunaan Bot

#### /start
```
Assalamu'alaikum, Rian! 👋

🕌 Selamat datang di Bot Pengingat Sholat.

Silakan pilih Kota / Wilayah Anda untuk mulai mengonfigurasi lokasi pengingat sholat:
[Tombol Inline Keyboard Muncul]
```

#### Setelah Pilih Kota (Contoh: Bandung)
```
✅ Lokasi berhasil di-set!

📍 Kota: Bandung
🕐 Zona Waktu: WIB (Asia/Jakarta)

Kamu akan menerima pengingat sholat.
Ketik /jadwal untuk melihat jadwal hari ini.
```

### /jadwal
```
🕌 Jadwal Sholat — Bandung
📅 Thursday, 27 March 2026
🕐 Zona Waktu: WIB

━━━━━━━━━━━━━━━━━━━━━━
  🌅  Subuh    →   04:37 WIB
  ☀️  Dzuhur   →   11:55 WIB
  🌤️  Ashar    →   15:12 WIB
  🌇  Maghrib  →   17:56 WIB
  🌙  Isya     →   19:06 WIB
━━━━━━━━━━━━━━━━━━━━━━

🔔 Reminder otomatis aktif (H-10 menit & tepat waktu)
```

### Reminder H-10
```
⏳ 10 menit lagi waktu sholat Maghrib di Bandung.

🕐 Pukul 17:56 WIB

Bersiap-siaplah untuk menunaikan sholat. 🤲
```

### Reminder Tepat Waktu
```
🕌 Waktu Sholat Maghrib

📍 Kota: Bandung
🕐 Waktu: 17:56 WIB

Saatnya menunaikan sholat Maghrib.
Semoga Allah menerima ibadah kita. 🤲

📖 "Sesungguhnya sholat itu mencegah dari perbuatan keji dan mungkar."
— Al-Quran (QS. Al-Ankabut: 45)
```

## 🔧 Fitur

- ✅ Set kota Indonesia (100+ kota didukung)
- ✅ 3 zona waktu (WIB, WITA, WIT)
- ✅ Cache Redis per kota (TTL 24 jam)
- ✅ Reminder H-10 menit & tepat waktu
- ✅ Quote islami random dari database
- ✅ Scheduler per kota (bukan per user)
- ✅ Redis lock untuk hindari duplikasi
- ✅ Retry mechanism pada API & pengiriman pesan
- ✅ Logging lengkap ke file & console
- ✅ Auto-refresh jadwal harian via Celery Beat

## 📋 Commands

| Command | Deskripsi |
|---------|-----------|
| `/start` | Mulai bot & Set Kota via Keyboard |
| `/jadwal` | Lihat jadwal sholat hari ini |
| `/info` | Lihat info akun dan lokasi |
| `/help` | Daftar perintah |
