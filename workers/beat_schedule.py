"""
Celery Beat periodic task schedule.
"""

from celery.schedules import crontab


def setup_beat_schedule(app):
    """
    Configure Celery Beat periodic tasks.

    Runs daily at 00:05 WIB to refresh prayer schedules for all registered cities.
    """
    app.conf.beat_schedule = {
        "refresh-all-city-schedules-daily": {
            "task": "workers.tasks.refresh_all_schedules",
            "schedule": crontab(minute=5, hour=0),  # 00:05 every day
            "options": {"queue": "default"},
        },
    }
