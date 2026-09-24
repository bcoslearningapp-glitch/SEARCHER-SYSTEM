"""Design synthesis HTTP API (PRD §32)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.modules.design_experiments import service
from research_api.modules.design_experiments.schemas import (
    ConceptIn,
    ConceptOut,
    CoverageIn,
    RejectIn,
    RequirementIn,
    RequirementOut,
    RequirementRevision,
    RequirementStatusIn,
    SelectIn,
    SelectOut,
    StatusIn,
    WithdrawIn,
)
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.governance_audit.schemas import GateEvaluationOut
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}/design", tags=["design"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/requirements", response_model=list[RequirementOut])
def list_requirements(project_id: UUID, db: DB, include_history: bool = False) -> list[RequirementOut]:
    return service.list_requirements(db, project_id, include_history=include_history)


@router.post("/requirements", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
def create_requirement(project_id: UUID, data: RequirementIn, db: DB, who: Who) -> RequirementOut:
    return service.create_requirement(db, who, project_id, data)


@router.get("/requirements/{requirement_id}/history", response_model=list[RequirementOut])
def requirement_history(project_id: UUID, requirement_id: UUID, db: DB) -> list[RequirementOut]:
    return service.requirement_history(db, project_id, requirement_id)


@router.post("/requirements/{requirement_id}/revise", response_model=RequirementOut)
def revise_requirement(
    project_id: UUID, requirement_id: UUID, data: RequirementRevision, db: DB, who: Who
) -> RequirementOut:
    return service.revise_requirement(db, who, project_id, requirement_id, data)


@router.post("/requirements/{requirement_id}/confirm", response_model=RequirementOut)
def confirm_requirement(
    project_id: UUID, requirement_id: UUID, data: RequirementStatusIn, db: DB, who: Who
) -> RequirementOut:
    return service.confirm_requirement(db, who, project_id, requirement_id, data.reason)


@router.post("/requirements/{requirement_id}/withdraw", response_model=RequirementOut)
def withdraw_requirement(project_id: UUID, requirement_id: UUID, data: WithdrawIn, db: DB, who: Who) -> RequirementOut:
    return service.withdraw_requirement(db, who, project_id, requirement_id, data.reason)


@router.get("/concepts", response_model=list[ConceptOut])
def list_concepts(project_id: UUID, db: DB) -> list[ConceptOut]:
    return service.list_concepts(db, project_id)


@router.post("/concepts", response_model=ConceptOut, status_code=status.HTTP_201_CREATED)
def create_concept(project_id: UUID, data: ConceptIn, db: DB, who: Who) -> ConceptOut:
    return service.create_concept(db, who, project_id, data)


@router.get("/concepts/{concept_id}", response_model=ConceptOut)
def get_concept(project_id: UUID, concept_id: UUID, db: DB) -> ConceptOut:
    return service.get_concept(db, project_id, concept_id)


@router.put("/concepts/{concept_id}/coverage", response_model=ConceptOut)
def set_coverage(project_id: UUID, concept_id: UUID, data: CoverageIn, db: DB, who: Who) -> ConceptOut:
    return service.set_coverage(db, who, project_id, concept_id, data)


@router.post("/concepts/{concept_id}/status", response_model=ConceptOut)
def set_status(project_id: UUID, concept_id: UUID, data: StatusIn, db: DB, who: Who) -> ConceptOut:
    return service.set_status(db, who, project_id, concept_id, data)


@router.get("/concepts/{concept_id}/readiness", response_model=GateEvaluationOut | None)
def latest_readiness(project_id: UUID, concept_id: UUID, db: DB) -> GateEvaluationOut | None:
    return service.latest_readiness(db, project_id, concept_id)


@router.post("/concepts/{concept_id}/readiness", response_model=GateEvaluationOut)
def evaluate_readiness(project_id: UUID, concept_id: UUID, db: DB, who: Who) -> GateEvaluationOut:
    return service.evaluate_readiness(db, who, project_id, concept_id)


@router.post("/concepts/{concept_id}/select", response_model=SelectOut)
def select_concept(project_id: UUID, concept_id: UUID, data: SelectIn, db: DB, who: Who) -> SelectOut:
    return service.select_concept(db, who, project_id, concept_id, data)


@router.post("/concepts/{concept_id}/reject", response_model=ConceptOut)
def reject_concept(project_id: UUID, concept_id: UUID, data: RejectIn, db: DB, who: Who) -> ConceptOut:
    return service.reject_concept(db, who, project_id, concept_id, data)
