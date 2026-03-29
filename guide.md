# Panduan Deploy ke VPS (Ubuntu)

Panduan singkat dari nol untuk menjalankan bot Telegram + Celery (worker & beat) di VPS.

## 1) Persiapan Server

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

Jika ingin pakai Docker Compose untuk PostgreSQL/Redis, install Docker + Compose sesuai distro.

## 2) Clone Project

```bash
cd /opt
sudo git clone <repo-url> pengingat-sholat
sudo chown -R $USER:$USER pengingat-sholat
cd pengingat-sholat
```

## 3) Konfigurasi `.env`

```bash
cp .env.example .env
nano .env
```

Wajib isi minimal:
- `TELEGRAM_BOT_TOKEN`
- `DATABASE_URL`
- `REDIS_URL`

Jika pakai `docker-compose.yml`, isi juga:
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`, `REDIS_PORT`.

## 4) Jalankan PostgreSQL + Redis (Docker Compose)

```bash
docker compose up -d
docker compose ps
```

## 5) Install Dependency Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 6) Migrasi & Seed Quotes

Jika DB sudah pernah dipakai, jalankan migrasi dulu.

```bash
source venv/bin/activate
python migrate_add_quote_category.py
python seed_quotes.py
```

Catatan: `seed_quotes.py` akan drop & recreate tabel `quotes`.

## 7) Jalankan dengan `systemd`

Buat 3 service:
- Bot: `venv/bin/python bot/main.py`
- Worker: `venv/bin/celery -A workers.celery_app worker --loglevel=info`
- Beat: `venv/bin/celery -A workers.celery_app beat --loglevel=info`

Minimal konfigurasi yang disarankan:
- `WorkingDirectory=/opt/pengingat-sholat`
- `EnvironmentFile=/opt/pengingat-sholat/.env`
- `Restart=always`

Aktifkan:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pengingat-sholat-bot pengingat-sholat-worker pengingat-sholat-beat
sudo journalctl -u pengingat-sholat-bot -f
```

