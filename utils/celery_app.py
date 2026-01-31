"""
Celery application configuration for async task processing.
"""
from celery import Celery
from utils.config import settings

# Create Celery app
celery_app = Celery(
    "crypto_analysis",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.ANALYSIS_TIMEOUT_SECONDS * 2,
    task_soft_time_limit=settings.ANALYSIS_TIMEOUT_SECONDS,
)

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(['engines', 'utils'])
