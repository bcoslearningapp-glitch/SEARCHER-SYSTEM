"""Task dispatch to the background worker (Celery on Redis, ADR-003).

The API only enqueues by task name; task implementations live in
services/worker. The broker carries job IDs, never job state.
"""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from celery import Celery

from research_api.config import get_settings


@lru_cache(maxsize=1)
def get_celery() -> Celery:
    settings = get_settings()
    app = Celery("research", broker=settings.redis_url)
    app.conf.update(
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_serializer="json",
        accept_content=["json"],
        broker_connection_retry_on_startup=True,
        broker_transport_options={"max_retries": 1},
        task_ignore_result=True,
    )
    return app


def dispatch(task_name: str, job_id: UUID) -> None:
    get_celery().send_task(task_name, args=[str(job_id)], retry=False)
