# 🕌 Bot Pengingat Sholat Indonesia

Bot Telegram pengingat waktu sholat 5 waktu untuk provinsi-provinsi di Indonesia. Menggunakan data dari [Aladhan API](https://aladhan.com/prayer-times-api).

## ⚙️ Tech Stack

| Teknologi           | Fungsi                                  |
| ------------------- | --------------------------------------- |
| Python 3.10+        | Bahasa utama                            |
| python-telegram-bot | Telegram Bot API (async)                |
| PostgreSQL          | Database (users, quotes)                |
| Redis               | Cache, message broker, distributed lock |
| Celery              | Task queue & worker                     |
| Celery Beat         | Scheduler harian                        |
| httpx               | HTTP client (Aladhan API)               |
| SQLAlchemy          | ORM                                     |
| Pillow              | Render gambar quote (`/quote`)          |

## 📁 Struktur Project

```
├── bot/
│   ├── handlers.py      # Command handlers (/start, /jadwal, /quote, /feedback, /help, /info)
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
│   ├── timezone.py      # Provinsi → timezone mapping
│   └── logger.py        # Logging configuration
├── logs/                # Log files
├── migrate_add_quote_category.py # Migrasi kolom quotes.category (sekali, jika DB lama)
├── seed_quotes.py       # Seed Islamic quotes ke DB
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Setup & Instalasi (Dari Nol)

### 1) Prerequisites

Pastikan sudah terinstall:

- **Python 3.10+**
- **PostgreSQL** + **Redis** (pilih salah satu: pakai Docker Compose atau install manual)

### 2) Clone Repository

```bash
git clone <repo-url> pengingat-sholat
cd pengingat-sholat
```

### 3) Konfigurasi Environment (.env)

```bash
# Windows:
copy .env.example .env

# Linux/Mac:
cp .env.example .env
```

Isi minimal:

- `TELEGRAM_BOT_TOKEN` → dari @BotFather
- `DATABASE_URL` → PostgreSQL connection string
- `REDIS_URL` → Redis connection string

Contoh `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=postgresql://postgres:password@localhost:5432/prayer_bot
REDIS_URL=redis://localhost:6379/0
```

### 4) Jalankan PostgreSQL + Redis (Opsional: Docker Compose)

Jika ingin cepat, gunakan `docker-compose.yml`:

```bash
docker compose up -d
```

Pastikan `.env` juga berisi variabel untuk compose:
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`, `REDIS_PORT`.

### 5) Virtual Environment + Install Dependencies

```bash
python -m venv venv

# Windows:
venv\\Scripts\\activate

# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 6) Migrasi & Seed Quotes

```bash
python migrate_add_quote_category.py
python seed_quotes.py
```

Catatan:

- `migrate_add_quote_category.py` diperlukan jika kamu punya DB lama (agar kolom `quotes.category` ada).
- `seed_quotes.py` akan drop & recreate tabel `quotes`.

## ▶️ Menjalankan (Local)

Jalankan 3 proses (disarankan 3 terminal):

### 1) Start Bot (Terminal 1)

```bash
python bot/main.py
```

### 2) Start Celery Worker (Terminal 2)

```bash
celery -A workers.celery_app worker --loglevel=info --pool=solo
```

> **Windows**: Gunakan `--pool=solo` karena Celery tidak support prefork di Windows.

### 3) Start Celery Beat (Terminal 3)

```bash
celery -A workers.celery_app beat --loglevel=info
```

## 🧑‍💻 Contoh Penggunaan Bot

#### /start

```
Assalamu'alaikum, Rian! 👋

🕌 Selamat datang di Bot Pengingat Sholat.

Silakan pilih Provinsi Anda untuk mulai mengonfigurasi lokasi pengingat sholat:
[Tombol Inline Keyboard Muncul]
```

#### Setelah Pilih Provinsi (Contoh: Jawa Barat)

```
✅ Lokasi berhasil di-set!

📍 Provinsi: Jawa Barat
🕐 Zona Waktu: WIB (Asia/Jakarta)

Kamu akan menerima pengingat sholat.
Ketik /jadwal untuk melihat jadwal hari ini.
```

### /jadwal

```
🕌 Jadwal Sholat — Jawa Barat
📅 Thursday, 27 March 2026
🕐 Zona Waktu: WIB

━━━━━━━━━━━━━━━━━━━━━━
  🌅  Subuh    →   04:37 WIB
  ☀️  Dzuhur   →   11:55 WIB
  🌤️  Ashar    →   15:12 WIB
  🌇  Maghrib  →   17:56 WIB
  🌙  Isya     →   19:06 WIB
━━━━━━━━━━━━━━━━━━━━━━

🔔 Reminder otomatis aktif (H-10 menit)
```

### Reminder H-10

```
⏳ 10 menit lagi waktu sholat Maghrib di Jawa Barat.

🕐 Pukul 17:56 WIB

Bersiap-siaplah untuk menunaikan sholat. 🤲
```

### Reminder Tepat Waktu

```
🕌 Waktu Sholat Maghrib

📍 Provinsi: Jawa Barat
🕐 Waktu: 17:56 WIB

Saatnya menunaikan sholat Maghrib.
Semoga Allah menerima ibadah kita. 🤲

📖 "Sesungguhnya sholat itu mencegah dari perbuatan keji dan mungkar."
— Al-Quran (QS. Al-Ankabut: 45)
```

## 🔧 Fitur

- ✅ Set provinsi Indonesia
- ✅ 3 zona waktu (WIB, WITA, WIT)
- ✅ Cache Redis per provinsi (TTL 24 jam)
- ✅ Reminder H-10 menit
- ✅ Quote islami random dari database
- ✅ Scheduler per provinsi (bukan per user)
- ✅ Redis lock untuk hindari duplikasi
- ✅ Retry mechanism pada API & pengiriman pesan
- ✅ Logging lengkap ke file & console
- ✅ Auto-refresh jadwal harian via Celery Beat

## 📋 Commands

| Command     | Deskripsi                             |
| ----------- | ------------------------------------- |
| `/start`    | Mulai bot & Set Provinsi via Keyboard |
| `/jadwal`   | Lihat jadwal sholat hari ini          |
| `/quote`    | Kirim quote islami random (gambar)    |
| `/info`     | Lihat info akun dan lokasi            |
| `/feedback` | Kirim masukkan/saran (hubungi admin)  |
| `/help`     | Daftar perintah                       |

## 🖥️ Deploy ke VPS

Lihat `guide.md` untuk panduan deploy dari nol ke VPS (Ubuntu) termasuk `systemd`.
