from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from research_api.contracts.enums import ActorKind
from research_api.modules.governance_audit import service as audit
from research_api.modules.governance_audit.models import ResearchEventRecord
from research_api.modules.governance_audit.schemas import Actor, ResearchEventEntry
from research_api.platform import jobs
from research_api.platform.db import session_scope
from research_worker import tasks
from research_worker.runner import run_job


def _new_job(**params: Any) -> UUID:
    with session_scope() as session:
        return jobs.create_job(session, "test", params=params).id


def _state(job_id: UUID) -> jobs.BackgroundJob:
    with session_scope() as session:
        return jobs.get_job(session, job_id)


def test_ping_task_round_trips_through_database() -> None:
    job_id = _new_job()
    assert tasks.ping(str(job_id)) == "SUCCEEDED"
    job = _state(job_id)
    assert job.result is not None and job.result["pong"] is True
    assert job.started_at is not None and job.finished_at is not None


def test_failed_body_rolls_back_partial_state() -> None:
    job_id = _new_job()
    marker = "PartialWrite" + "".join(chr(ord("a") + int(c, 16)) for c in job_id.hex[:8])

    def body(session: Session, job: jobs.BackgroundJob) -> dict[str, Any]:
        audit.record_research_event(
            session, ResearchEventEntry(event_type=marker, actor=Actor(kind=ActorKind.SYSTEM, id="worker"))
        )
        raise RuntimeError("provider exploded mid-task")

    assert run_job(job_id, body) is jobs.JobState.FAILED
    job = _state(job_id)
    assert job.failure_kind == "APPLICATION_ERROR"
    assert "exploded" in (job.error or "")
    with session_scope() as session:
        count = session.scalar(
            select(func.count())
            .select_from(ResearchEventRecord)
            .where(ResearchEventRecord.event_type == marker)
        )
    assert count == 0


def test_non_queued_job_is_not_rerun() -> None:
    job_id = _new_job()
    with session_scope() as session:
        jobs.request_cancel(jobs.get_job(session, job_id))
    calls: list[int] = []
    assert run_job(job_id, lambda s, j: calls.append(1) or {}) is jobs.JobState.CANCELLED
    assert calls == []


def test_cancel_requested_while_running_ends_cancelled() -> None:
    job_id = _new_job()

    def body(session: Session, job: jobs.BackgroundJob) -> dict[str, Any]:
        with session_scope() as other:
            jobs.request_cancel(jobs.get_job(other, job_id, for_update=True))
        return {"done": True}

    assert run_job(job_id, body) is jobs.JobState.CANCELLED
