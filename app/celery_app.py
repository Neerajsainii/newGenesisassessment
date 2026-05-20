from celery import Celery

from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


celery_app = Celery(
    "scalable_data_api",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

