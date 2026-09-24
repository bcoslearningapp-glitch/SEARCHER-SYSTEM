"""Decision records HTTP API (FR-DEC-001/002)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from research_api.contracts.enums import DecisionStatus
from research_api.modules.governance_audit import service
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.governance_audit.schemas import DecisionCreate, DecisionOut, DecisionResolve
from research_api.platform.db import get_session

router = APIRouter(prefix="/api/v1/projects/{project_id}/decisions", tags=["decisions"])

DB = Annotated[Session, Depends(get_session)]
Who = Annotated[Principal, Depends(current_principal)]


class WithdrawIn(BaseModel):
    reason: str = Field(min_length=1)


@router.get("", response_model=list[DecisionOut])
def list_decisions(project_id: UUID, db: DB, status: DecisionStatus | None = None) -> list[DecisionOut]:
    return service.list_decisions(db, project_id, status=status)


@router.post("", response_model=DecisionOut, status_code=status.HTTP_201_CREATED)
def create_decision(project_id: UUID, data: DecisionCreate, db: DB, who: Who) -> DecisionOut:
    return service.create_decision(db, who, project_id, data)


@router.get("/{decision_id}", response_model=DecisionOut)
def get_decision(project_id: UUID, decision_id: UUID, db: DB) -> DecisionOut:
    return service.get_decision(db, project_id, decision_id)


@router.post("/{decision_id}/resolve", response_model=DecisionOut)
def resolve(project_id: UUID, decision_id: UUID, data: DecisionResolve, db: DB, who: Who) -> DecisionOut:
    return service.resolve_decision(db, who, project_id, decision_id, data)


@router.post("/{decision_id}/withdraw", response_model=DecisionOut)
def withdraw(project_id: UUID, decision_id: UUID, data: WithdrawIn, db: DB, who: Who) -> DecisionOut:
    return service.withdraw_decision(db, who, project_id, decision_id, data.reason)
