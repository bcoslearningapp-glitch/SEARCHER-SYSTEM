"""Hypothesis lab HTTP API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.hypothesis_lab import service
from research_api.modules.hypothesis_lab.schemas import (
    AssessIn,
    CompeteIn,
    HypothesisIn,
    HypothesisOut,
    LinkMechanismIn,
    MechanismIn,
    MechanismOut,
    MechanismUpdate,
    ReviseIn,
    TransitionIn,
    TransitionOut,
    VersionOut,
)
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["hypotheses"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/hypotheses", response_model=list[HypothesisOut])
def list_hypotheses(project_id: UUID, db: DB) -> list[HypothesisOut]:
    return service.list_hypotheses(db, project_id)


@router.post("/hypotheses", response_model=HypothesisOut, status_code=status.HTTP_201_CREATED)
def create_hypothesis(project_id: UUID, data: HypothesisIn, db: DB, who: Who) -> HypothesisOut:
    return service.create_hypothesis(db, who, project_id, data)


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisOut)
def get_hypothesis(project_id: UUID, hypothesis_id: UUID, db: DB) -> HypothesisOut:
    return service.get_hypothesis(db, project_id, hypothesis_id)


@router.get("/hypotheses/{hypothesis_id}/versions", response_model=list[VersionOut])
def versions(project_id: UUID, hypothesis_id: UUID, db: DB) -> list[VersionOut]:
    return service.list_versions(db, project_id, hypothesis_id)


@router.post("/hypotheses/{hypothesis_id}/revise", response_model=HypothesisOut)
def revise(project_id: UUID, hypothesis_id: UUID, data: ReviseIn, db: DB, who: Who) -> HypothesisOut:
    return service.revise(db, who, project_id, hypothesis_id, data)


@router.post("/hypotheses/{hypothesis_id}/transition", response_model=TransitionOut)
def transition(project_id: UUID, hypothesis_id: UUID, data: TransitionIn, db: DB, who: Who) -> TransitionOut:
    return service.transition(db, who, project_id, hypothesis_id, data)


@router.post("/hypotheses/{hypothesis_id}/assess", response_model=HypothesisOut)
def assess(project_id: UUID, hypothesis_id: UUID, data: AssessIn, db: DB, who: Who) -> HypothesisOut:
    return service.assess(db, who, project_id, hypothesis_id, data)


@router.post("/hypotheses/{hypothesis_id}/competing", response_model=HypothesisOut)
def compete(project_id: UUID, hypothesis_id: UUID, data: CompeteIn, db: DB, who: Who) -> HypothesisOut:
    return service.compete(db, who, project_id, hypothesis_id, data)


@router.post("/hypotheses/{hypothesis_id}/mechanisms", response_model=HypothesisOut)
def link_mechanism(project_id: UUID, hypothesis_id: UUID, data: LinkMechanismIn, db: DB, who: Who) -> HypothesisOut:
    return service.link_mechanism(db, who, project_id, hypothesis_id, data.mechanism_id)


@router.get("/mechanisms", response_model=list[MechanismOut])
def list_mechanisms(project_id: UUID, db: DB) -> list[MechanismOut]:
    return service.list_mechanisms(db, project_id)


@router.post("/mechanisms", response_model=MechanismOut, status_code=status.HTTP_201_CREATED)
def create_mechanism(project_id: UUID, data: MechanismIn, db: DB, who: Who) -> MechanismOut:
    return service.create_mechanism(db, who, project_id, data)


@router.patch("/mechanisms/{mechanism_id}", response_model=MechanismOut)
def update_mechanism(project_id: UUID, mechanism_id: UUID, data: MechanismUpdate, db: DB, who: Who) -> MechanismOut:
    return service.update_mechanism(db, who, project_id, mechanism_id, data)
