"""Research Orchestrator HTTP API: launch AI tasks as background jobs and follow them."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.research_orchestrator import service
from research_api.modules.research_orchestrator.service import AITaskIn
from research_api.platform import jobs, queue
from research_api.platform.db import DBSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects/{project_id}/ai-tasks", tags=["research orchestrator"])

Who = Annotated[Principal, Depends(current_principal)]


@router.post("", response_model=jobs.JobOut, status_code=status.HTTP_202_ACCEPTED)
def launch(project_id: UUID, data: AITaskIn, db: DBSession, who: Who) -> jobs.JobOut:
    """Queue an AI task. Status lives in the database, independent of the browser (FR-ORCH-005)."""
    job = service.launch(db, who, project_id, data)
    db.commit()  # the worker must see the job before it is dispatched
    try:
        queue.dispatch(service.WORKER_TASK, job.id)
    except Exception as exc:
        logger.warning("dispatch failed for AI task job %s", job.id, exc_info=True)
        jobs.transition(job, jobs.JobState.FAILED, failure_kind=jobs.JobFailureKind.DISPATCH_FAILURE, error=str(exc))
        db.commit()
    return jobs.JobOut.model_validate(job)


@router.get("", response_model=list[jobs.JobOut])
def list_tasks(project_id: UUID, db: DBSession) -> list[jobs.JobOut]:
    return service.list_tasks(db, project_id)
