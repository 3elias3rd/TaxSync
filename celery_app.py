from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "REDIS://REDIS:6379")

# Celery app -- Redis as both broker and result backend
celery = Celery(
    "taxsync",
    broker = REDIS_URL,
    backend = REDIS_URL,
    include = ["tasks.expense_tasks", "tasks.tax_tasks", "tasks.audit_tasks"]
)

celery.conf.update(
    task_serializer = "json",
    result_serializer = "json",
    accept_content = ["json"],
    timezone = "Asia/Dubai",
    enable_utc =  True,

    # Scheduled tasks - Celery Beat
    beat_schedule = {
        "precalculate-tax-reports": {
            "task": "tasks.tax_tasks.preculculate_tax_reports",
            "schedule": crontab(hour=2, minute=0), # To run at 2am daily
        }
    }
)