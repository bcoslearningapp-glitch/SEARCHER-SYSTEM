"""'Needs Your Attention' queue (PRD §65): approvals, blocking decisions, access requests, due revalidations.

Aggregates other modules through their public services only.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    DecisionStatus,
    NotificationLevel,
    ProblemFrameStatus,
    SourceAccessRequestStatus,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.knowledge_memory import service as knowledge
from research_api.modules.project_workflow import service as projects
from research_api.modules.sources_library import service as sources
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["attention"])

_LEVEL_ORDER = [NotificationLevel.BLOCKING, NotificationLevel.DECISION_REQUIRED, NotificationLevel.ATTENTION]


class AttentionItem(BaseModel):
    kind: str
    level: NotificationLevel
    title: str
    entity_type: str
    entity_id: UUID


def attention_queue(session: Session, project_id: UUID) -> list[AttentionItem]:
    projects.get_project(session, project_id)
    items: list[AttentionItem] = []
    for frame in projects.list_frames(session, project_id):
        if frame.status is ProblemFrameStatus.DRAFT:
            items.append(
                AttentionItem(
                    kind="approval",
                    level=NotificationLevel.DECISION_REQUIRED,
                    title=f"Problem Frame v{frame.version_number} awaits your approval",
                    entity_type="ProblemFrameVersion",
                    entity_id=frame.id,
                )
            )
    for decision in governance.list_decisions(session, project_id, status=DecisionStatus.OPEN):
        items.append(
            AttentionItem(
                kind="decision",
                level=NotificationLevel.BLOCKING if decision.blocking else NotificationLevel.DECISION_REQUIRED,
                title=decision.question,
                entity_type="Decision",
                entity_id=decision.id,
            )
        )
    for status in (SourceAccessRequestStatus.OPEN, SourceAccessRequestStatus.PARTIALLY_FULFILLED):
        for request in sources.list_access_requests(session, project_id, status=status):
            items.append(
                AttentionItem(
                    kind="source_access_request",
                    level=NotificationLevel.ATTENTION,
                    title=f"Source access needed: {request.requested_scope}",
                    entity_type="SourceAccessRequest",
                    entity_id=request.id,
                )
            )
    for item in knowledge.revalidation_due(session, project_id):
        items.append(
            AttentionItem(
                kind="revalidation",
                level=NotificationLevel.ATTENTION,
                title=f"Knowledge needs revalidation: {item.statement[:120]}",
                entity_type="KnowledgeItem",
                entity_id=item.id,
            )
        )
    return sorted(items, key=lambda i: _LEVEL_ORDER.index(i.level))


@router.get("/attention", response_model=list[AttentionItem])
def get_attention(project_id: UUID, db: DBSession) -> list[AttentionItem]:
    return attention_queue(db, project_id)
