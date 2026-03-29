"""
Celery application configuration.
"""

from celery import Celery
from config.settings import settings

celery_app = Celery(
    "prayer_bot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks"],
)

celery_app.conf.update(
    # Timezone
    timezone="Asia/Jakarta",
    enable_utc=True,

    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Task time limits
    task_soft_time_limit=120,
    task_time_limit=180,

    # Result expiry
    result_expires=3600,
)

# Import beat schedule
from workers.beat_schedule import setup_beat_schedule  # noqa: E402
setup_beat_schedule(celery_app)
