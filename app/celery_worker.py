from app.celery_tasks import celery

# Start the worker with:
# celery -A celery_worker.celery worker --loglevel=info
