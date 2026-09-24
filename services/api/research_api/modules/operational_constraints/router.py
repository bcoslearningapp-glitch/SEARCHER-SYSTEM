"""Operational constraints and combined standing HTTP API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.contracts.enums import EvidenceTargetType
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.operational_constraints import service
from research_api.modules.operational_constraints.schemas import ConstraintIn, ConstraintOut, ResolveIn, TargetStanding
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["operational constraints"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.post("/operational-constraints", response_model=ConstraintOut, status_code=status.HTTP_201_CREATED)
def add_constraint(project_id: UUID, data: ConstraintIn, db: DB, who: Who) -> ConstraintOut:
    return service.add_constraint(db, who, project_id, data)


@router.post("/operational-constraints/{constraint_id}/resolve", response_model=ConstraintOut)
def resolve(project_id: UUID, constraint_id: UUID, data: ResolveIn, db: DB, who: Who) -> ConstraintOut:
    return service.resolve_constraint(db, who, project_id, constraint_id, data)


@router.get("/standing/{target_type}/{target_id}", response_model=TargetStanding)
def standing(project_id: UUID, target_type: EvidenceTargetType, target_id: UUID, db: DB) -> TargetStanding:
    return service.target_standing(db, project_id, target_type, target_id)
