import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Add the 'include' array right here
celery_app = Celery(
    "incomeproof",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.process_statement"] 
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,      
    task_soft_time_limit=240, 
    task_acks_late=True,      
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
)

# You can completely delete the autodiscover_tasks line!