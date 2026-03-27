from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

celery = Celery(
    "taxsync",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.expense_tasks", "tasks.tax_tasks", "tasks.audit_tasks"]
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Dubai",
    enable_utc=True,

    beat_schedule={
        "precalculate-tax-reports": {
            "task": "tasks.tax_tasks.precalculate_tax_reports",
            "schedule": crontab(hour=2, minute=0),
        }
    }
)