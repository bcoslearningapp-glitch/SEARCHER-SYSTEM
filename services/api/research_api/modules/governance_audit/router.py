"""Read-only audit API. Audit is written only by domain services, never by clients."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from research_api.modules.governance_audit import service
from research_api.modules.governance_audit.schemas import AuditEventOut
from research_api.platform.db import get_session

router = APIRouter(prefix="/api/v1/audit-events", tags=["audit"])


@router.get("", response_model=list[AuditEventOut])
def list_audit_events(
    session: Annotated[Session, Depends(get_session)],
    project_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditEventOut]:
    return service.list_audit_events(session, project_id=project_id, limit=limit)
