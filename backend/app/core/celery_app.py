"""
Celery app for background jobs -- currently just rank recomputation,
but this is the place to add report generation, bulk notification
sending, etc. as the system grows.
"""
import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "physical_eval_portal",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Eager mode runs .delay() calls synchronously in-process instead of
# dispatching to a Redis broker for a worker to pick up -- no Redis, no
# separate worker process required. This exists specifically for
# deployments without a dedicated background-worker process (e.g. a
# single free-tier web service), where the trade-off (rank recompute
# blocks the request briefly, same as it did before Celery was
# introduced) is worth not paying for/running a worker. Real deployments
# with a `celery_worker` process (docker-compose.yml / .prod.yml) should
# leave this unset -- FALSE -- to get true background execution.
if os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true":
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    # Ranking recompute is idempotent (RANK() OVER recomputes fresh each
    # time), so at-least-once delivery is fine -- no need for stricter
    # exactly-once guarantees here.
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "reconcile-all-ranks-every-15-minutes": {
            "task": "tasks.reconcile_all_ranks",
            "schedule": 900.0,  # seconds
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
