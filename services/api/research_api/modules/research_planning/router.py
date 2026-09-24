"""Research planning HTTP API: plans, local search with audit, and sufficiency."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.research_planning import service
from research_api.modules.research_planning.schemas import (
    LocalSearchIn,
    LocalSearchOut,
    PlanIn,
    PlanOut,
    PlanOverview,
    PlanRevision,
    SufficiencyIn,
    SufficiencyOut,
)
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["research planning"])

Who = Annotated[Principal, Depends(current_principal)]


@router.post("/research-plans", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(project_id: UUID, data: PlanIn, db: DBSession, who: Who) -> PlanOut:
    return service.create_plan(db, who, project_id, data)


@router.get("/research-plans", response_model=list[PlanOut])
def list_plans(project_id: UUID, db: DBSession) -> list[PlanOut]:
    return service.list_plans(db, project_id)


@router.get("/research-plans/{plan_id}", response_model=PlanOverview)
def plan_overview(project_id: UUID, plan_id: UUID, db: DBSession) -> PlanOverview:
    return service.overview(db, project_id, plan_id)


@router.post("/research-plans/{plan_id}/revise", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def revise_plan(project_id: UUID, plan_id: UUID, data: PlanRevision, db: DBSession, who: Who) -> PlanOut:
    return service.revise_plan(db, who, project_id, plan_id, data)


@router.post("/searches/local", response_model=LocalSearchOut)
def local_search(project_id: UUID, data: LocalSearchIn, db: DBSession, who: Who) -> LocalSearchOut:
    return service.local_search(db, who, project_id, data)


@router.post(
    "/research-plans/{plan_id}/sufficiency", response_model=SufficiencyOut, status_code=status.HTTP_201_CREATED
)
def assess(project_id: UUID, plan_id: UUID, data: SufficiencyIn, db: DBSession, who: Who) -> SufficiencyOut:
    return service.assess_sufficiency(db, who, project_id, plan_id, data)
