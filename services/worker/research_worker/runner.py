"""Run a job body with durable status bookkeeping.

The body runs in its own transaction after the job is marked RUNNING, so a
failing body never leaves partial state behind (NFR-REL-003): its changes roll
back and the job records a distinguishable failure kind.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from research_api.platform import jobs
from research_api.platform.db import session_scope

logger = logging.getLogger(__name__)

JobBody = Callable[[Session, jobs.BackgroundJob], dict[str, Any]]


def run_job(job_id: UUID, body: JobBody) -> jobs.JobState:
    with session_scope() as session:
        job = jobs.get_job(session, job_id, for_update=True)
        if jobs.JobState(job.state) is not jobs.JobState.QUEUED:
            logger.info("job %s is %s; skipping", job_id, job.state)
            return jobs.JobState(job.state)
        jobs.transition(job, jobs.JobState.RUNNING)

    try:
        with session_scope() as session:
            job = jobs.get_job(session, job_id)
            result = body(session, job)
    except Exception as exc:
        logger.exception("job %s failed", job_id)
        with session_scope() as session:
            job = jobs.get_job(session, job_id, for_update=True)
            jobs.transition(
                job, jobs.JobState.FAILED, failure_kind=jobs.JobFailureKind.APPLICATION_ERROR, error=str(exc)
            )
        return jobs.JobState.FAILED

    with session_scope() as session:
        job = jobs.get_job(session, job_id, for_update=True)
        if job.cancel_requested:
            jobs.transition(job, jobs.JobState.CANCELLED)
        else:
            jobs.transition(job, jobs.JobState.SUCCEEDED, result=result)
        return jobs.JobState(job.state)
