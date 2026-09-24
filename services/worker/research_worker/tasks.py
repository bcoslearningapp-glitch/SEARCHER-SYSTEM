"""Task registry. Task names are the stable contract between API and worker."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from research_api.platform import jobs
from research_api.platform.queue import get_celery
from research_worker.runner import run_job

celery_app = get_celery()


def _ping_body(session: Session, job: jobs.BackgroundJob) -> dict[str, Any]:
    database_time = session.execute(text("SELECT now()")).scalar_one()
    return {"pong": True, "database_time": database_time.isoformat()}


@celery_app.task(name="system.ping")  # type: ignore[untyped-decorator]
def ping(job_id: str) -> str:
    return run_job(UUID(job_id), _ping_body).value
