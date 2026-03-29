# Repository Guidelines

## Project Structure & Module Organization

- `bot/`: entry point dan handler Telegram (`main.py`, `handlers.py`).
- `config/`: konfigurasi berbasis environment (`settings.py`).
- `models/`: SQLAlchemy ORM (mis. `user.py`, `quote.py`, `base.py`).
- `services/`: integrasi eksternal & domain logic (Aladhan API, cache Redis, perhitungan jadwal).
- `workers/`: Celery app, tasks, dan schedule Celery Beat.
- `utils/`: helper seperti logger dan mapping timezone.
- `logs/`: output log runtime (tidak perlu di-commit).
- Root scripts: `create_db.py`, `seed_quotes.py`, `check_quotes.py`.

## Build, Test, and Development Commands

- Setup venv + deps: `python -m venv venv` lalu `pip install -r requirements.txt`.
- Konfigurasi env: `copy .env.example .env` lalu isi `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `REDIS_URL` (lihat `README.md`).
- Jalankan bot: `python bot/main.py`.
- Celery worker: `celery -A workers.celery_app worker --loglevel=info --pool=solo` (Windows perlu `--pool=solo`).
- Celery beat: `celery -A workers.celery_app beat --loglevel=info`.
- Database setup: `python create_db.py` (sekali), lalu `python seed_quotes.py`.
- Dev infra (opsional): `docker compose up -d` untuk PostgreSQL + Redis (butuh `.env` yang berisi variabel compose).

## Coding Style & Naming Conventions

- Python 3.10+; gunakan indent 4 spasi dan import berurutan (stdlib → third-party → local).
- Modul/folder pakai `snake_case`; class `PascalCase`; fungsi/variabel `snake_case`.
- Pertahankan pola async yang dipakai `python-telegram-bot` (hindari blocking I/O; gunakan `httpx` untuk request).

## Testing Guidelines

- Belum ada framework test. Lakukan smoke test dengan menjalankan bot + worker + beat.
- Script bantu: `python check_quotes.py` untuk verifikasi random quote.

## Commit & Pull Request Guidelines

- Repo belum memiliki commit history; gunakan pesan commit ringkas dan imperatif (mis. `feat: add city picker`, `fix: handle redis timeout`).
- PR sebaiknya menyertakan: ringkasan perubahan, langkah verifikasi lokal, dan perubahan konfigurasi/env bila ada.

## Security & Configuration Tips

- Jangan commit `.env`, token Telegram, atau kredensial database/Redis.
- Jika menambah variabel baru, update `.env.example` dan dokumentasikan di `README.md`.
