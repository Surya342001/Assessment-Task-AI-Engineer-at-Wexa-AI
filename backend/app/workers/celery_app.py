
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "analytics_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.event_tasks",
        "app.workers.alert_tasks",
        "app.workers.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Retry config
    task_max_retries=3,
    task_default_retry_delay=60,
    # Celery Beat schedule
    beat_schedule={
        "evaluate-alerts-every-minute": {
            "task": "app.workers.alert_tasks.evaluate_all_alerts",
            "schedule": 60.0,  # every 60 seconds
        },
        "run-scheduled-reports-daily": {
            "task": "app.workers.report_tasks.run_due_reports",
            "schedule": crontab(minute="*/5"),  # check every 5 minutes
        },
    },
)
