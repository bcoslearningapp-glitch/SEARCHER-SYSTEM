"""System endpoints for background-job status (FR-ORCH-004/005)."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from research_api.platform import jobs, queue
from research_api.platform.db import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/system", tags=["system"])

PING_TASK = "system.ping"


@router.post("/jobs/ping", response_model=jobs.JobOut, status_code=status.HTTP_202_ACCEPTED)
def enqueue_ping(session: Annotated[Session, Depends(get_session)]) -> jobs.JobOut:
    """Round-trip API -> queue -> worker -> database. Used by smoke tests."""
    job = jobs.create_job(session, PING_TASK)
    session.commit()
    try:
        queue.dispatch(PING_TASK, job.id)
    except Exception as exc:
        logger.warning("dispatch failed for job %s", job.id, exc_info=True)
        jobs.transition(job, jobs.JobState.FAILED, failure_kind=jobs.JobFailureKind.DISPATCH_FAILURE, error=str(exc))
        session.commit()
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            {"message": "background queue unavailable", "job_id": str(job.id)},
        ) from exc
    return jobs.JobOut.model_validate(job)


@router.get("/jobs/{job_id}", response_model=jobs.JobOut)
def get_job(job_id: UUID, session: Annotated[Session, Depends(get_session)]) -> jobs.JobOut:
    try:
        return jobs.JobOut.model_validate(jobs.get_job(session, job_id))
    except jobs.JobNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found") from exc


@router.post("/jobs/{job_id}/cancel", response_model=jobs.JobOut)
def cancel_job(job_id: UUID, session: Annotated[Session, Depends(get_session)]) -> jobs.JobOut:
    try:
        job = jobs.get_job(session, job_id, for_update=True)
    except jobs.JobNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found") from exc
    jobs.request_cancel(job)
    return jobs.JobOut.model_validate(job)
