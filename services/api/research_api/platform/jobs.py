"""Durable background-job status (NFR-REL-002, FR-ORCH-005).

Job state lives in PostgreSQL, not in the broker or the browser, so status
survives worker restarts and page reloads. Transitions are explicit and
validated; illegal transitions raise instead of silently overwriting state.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class JobState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobFailureKind(StrEnum):
    """Keeps application, provider, and dispatch failures distinguishable (PRD §72)."""

    DISPATCH_FAILURE = "DISPATCH_FAILURE"
    APPLICATION_ERROR = "APPLICATION_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    STOPPED_RESOURCE_CONSTRAINT = "STOPPED_RESOURCE_CONSTRAINT"


TERMINAL_STATES = frozenset({JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED})

_ALLOWED: dict[JobState, frozenset[JobState]] = {
    JobState.QUEUED: frozenset({JobState.RUNNING, JobState.FAILED, JobState.CANCELLED}),
    JobState.RUNNING: frozenset({JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}),
    JobState.SUCCEEDED: frozenset(),
    JobState.FAILED: frozenset(),
    JobState.CANCELLED: frozenset(),
}


class IllegalJobTransitionError(Exception):
    pass


class JobNotFoundError(Exception):
    pass


class BackgroundJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "background_jobs"

    kind: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(20), default=JobState.QUEUED.value, index=True)
    project_id: Mapped[UUID | None] = mapped_column(index=True)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    failure_kind: Mapped[str | None] = mapped_column(String(40))
    error: Mapped[str | None] = mapped_column(Text)
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    state: JobState
    project_id: UUID | None
    params: dict[str, Any]
    result: dict[str, Any] | None
    failure_kind: JobFailureKind | None
    error: str | None
    cancel_requested: bool
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


def create_job(
    session: Session, kind: str, *, params: dict[str, Any] | None = None, project_id: UUID | None = None
) -> BackgroundJob:
    job = BackgroundJob(kind=kind, params=params or {}, project_id=project_id, state=JobState.QUEUED.value)
    session.add(job)
    session.flush()
    return job


def get_job(session: Session, job_id: UUID, *, for_update: bool = False) -> BackgroundJob:
    job = session.get(BackgroundJob, job_id, with_for_update=for_update)
    if job is None:
        raise JobNotFoundError(str(job_id))
    return job


def transition(
    job: BackgroundJob,
    new_state: JobState,
    *,
    result: dict[str, Any] | None = None,
    failure_kind: JobFailureKind | None = None,
    error: str | None = None,
) -> None:
    current = JobState(job.state)
    if new_state not in _ALLOWED[current]:
        raise IllegalJobTransitionError(f"{current} -> {new_state}")
    if new_state is JobState.FAILED and failure_kind is None:
        raise ValueError("FAILED jobs must record a failure_kind")
    job.state = new_state.value
    now = utcnow()
    if new_state is JobState.RUNNING:
        job.started_at = now
    if new_state in TERMINAL_STATES:
        job.finished_at = now
    if result is not None:
        job.result = result
    if failure_kind is not None:
        job.failure_kind = failure_kind.value
        job.error = error


def request_cancel(job: BackgroundJob) -> None:
    """Queued jobs cancel immediately; running jobs are asked to stop cooperatively."""
    if JobState(job.state) is JobState.QUEUED:
        transition(job, JobState.CANCELLED)
    elif JobState(job.state) is JobState.RUNNING:
        job.cancel_requested = True
