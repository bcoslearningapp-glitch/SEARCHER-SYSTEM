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

from research_api.modules.ai_gateway.base import ProviderError
from research_api.modules.ai_gateway.service import ResourceConstraintError
from research_api.platform import jobs
from research_api.platform.db import session_scope

logger = logging.getLogger(__name__)

JobBody = Callable[[Session, jobs.BackgroundJob], dict[str, Any]]
FailureHook = Callable[[Session, jobs.BackgroundJob], None]


def failure_kind(exc: Exception) -> jobs.JobFailureKind:
    """Keep provider failures and budget stops distinguishable from application errors (PRD §72)."""
    if isinstance(exc, ResourceConstraintError):
        return jobs.JobFailureKind.STOPPED_RESOURCE_CONSTRAINT
    if isinstance(exc, ProviderError):
        return jobs.JobFailureKind.PROVIDER_ERROR
    return jobs.JobFailureKind.APPLICATION_ERROR


def run_job(job_id: UUID, body: JobBody, on_failure: FailureHook | None = None) -> jobs.JobState:
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
    except jobs.JobCancelledError:
        logger.info("job %s cancelled cooperatively; its changes were rolled back", job_id)
        with session_scope() as session:
            jobs.transition(jobs.get_job(session, job_id, for_update=True), jobs.JobState.CANCELLED)
        return jobs.JobState.CANCELLED
    except Exception as exc:
        logger.exception("job %s failed", job_id)
        with session_scope() as session:
            job = jobs.get_job(session, job_id, for_update=True)
            jobs.transition(job, jobs.JobState.FAILED, failure_kind=failure_kind(exc), error=str(exc))
            if on_failure is not None:
                try:
                    with session.begin_nested():
                        on_failure(session, job)
                except Exception:
                    # The job must still end FAILED even if follow-up bookkeeping cannot be written.
                    logger.exception("failure hook for job %s failed", job_id)
        return jobs.JobState.FAILED

    with session_scope() as session:
        job = jobs.get_job(session, job_id, for_update=True)
        if job.cancel_requested:
            jobs.transition(job, jobs.JobState.CANCELLED)
        else:
            jobs.transition(job, jobs.JobState.SUCCEEDED, result=result)
        return jobs.JobState(job.state)
