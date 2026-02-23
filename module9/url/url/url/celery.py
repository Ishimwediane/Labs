import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "url.settings")

app = Celery("url")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "cleanup-expired-urls-nightly": {
        "task": "shortener.tasks.cleanup_expired_urls",
        "schedule": 86400.0,  # every 24 hours
}}