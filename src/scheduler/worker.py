from celery import Celery
from src.core.config import settings

app = Celery("grc_suite", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "run-all-controls-hourly": {
            "task": "src.scheduler.tasks.run_all_controls",
            "schedule": 3600.0,
        },
    },
)
