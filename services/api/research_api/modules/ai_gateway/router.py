"""AI gateway HTTP API: provider profiles, per-project AI policy and the disclosure log."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from research_api.modules.ai_gateway import service
from research_api.modules.ai_gateway.schemas import AIPolicyOut, AIPolicyUpdate, AIRequestOut, ProfileOut
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1", tags=["ai gateway"])

Who = Annotated[Principal, Depends(current_principal)]


@router.get("/ai/profiles", response_model=list[ProfileOut])
def list_profiles() -> list[ProfileOut]:
    """Configured model profiles. Never returns keys."""
    return service.list_profiles()


@router.get("/projects/{project_id}/ai-policy", response_model=AIPolicyOut)
def get_policy(project_id: UUID, db: DBSession) -> AIPolicyOut:
    return service.get_policy(db, project_id)


@router.put("/projects/{project_id}/ai-policy", response_model=AIPolicyOut)
def update_policy(project_id: UUID, data: AIPolicyUpdate, db: DBSession, who: Who) -> AIPolicyOut:
    return service.update_policy(db, who, project_id, data)


@router.get("/projects/{project_id}/ai-requests", response_model=list[AIRequestOut])
def list_requests(project_id: UUID, db: DBSession) -> list[AIRequestOut]:
    return service.list_requests(db, project_id)
