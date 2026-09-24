"""Design hypothesis and experiment HTTP API (PRD §33-34)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.contracts.enums import ExperimentState
from research_api.modules.design_experiments import experiment_service as service
from research_api.modules.design_experiments.experiment_schemas import (
    DesignHypothesisAssess,
    DesignHypothesisIn,
    DesignHypothesisOut,
    DesignHypothesisRevision,
    ExperimentIn,
    ExperimentOut,
    ExperimentRecordOut,
    ExperimentTransitionIn,
    ExperimentTransitionOut,
    ImpactIn,
    ImpactOut,
    InterpretationIn,
    InterpretationOut,
    ObservationIn,
    ObservationOut,
    ProtocolUpdate,
    ResultIn,
    ResultOut,
)
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.governance_audit.schemas import GateEvaluationOut
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["experiments"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/design-hypotheses", response_model=list[DesignHypothesisOut])
def list_design_hypotheses(project_id: UUID, db: DB) -> list[DesignHypothesisOut]:
    return service.list_design_hypotheses(db, project_id)


@router.post("/design-hypotheses", response_model=DesignHypothesisOut, status_code=status.HTTP_201_CREATED)
def create_design_hypothesis(project_id: UUID, data: DesignHypothesisIn, db: DB, who: Who) -> DesignHypothesisOut:
    return service.create_design_hypothesis(db, who, project_id, data)


@router.get("/design-hypotheses/{dh_id}", response_model=DesignHypothesisOut)
def get_design_hypothesis(project_id: UUID, dh_id: UUID, db: DB) -> DesignHypothesisOut:
    return service.get_design_hypothesis(db, project_id, dh_id)


@router.post("/design-hypotheses/{dh_id}/revise", response_model=DesignHypothesisOut)
def revise_design_hypothesis(
    project_id: UUID, dh_id: UUID, data: DesignHypothesisRevision, db: DB, who: Who
) -> DesignHypothesisOut:
    return service.revise_design_hypothesis(db, who, project_id, dh_id, data)


@router.post("/design-hypotheses/{dh_id}/assess", response_model=DesignHypothesisOut)
def assess_design_hypothesis(
    project_id: UUID, dh_id: UUID, data: DesignHypothesisAssess, db: DB, who: Who
) -> DesignHypothesisOut:
    return service.assess_design_hypothesis(db, who, project_id, dh_id, data)


@router.get("/experiments", response_model=list[ExperimentOut])
def list_experiments(project_id: UUID, db: DB) -> list[ExperimentOut]:
    return service.list_experiments(db, project_id)


@router.post("/experiments", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
def create_experiment(project_id: UUID, data: ExperimentIn, db: DB, who: Who) -> ExperimentOut:
    return service.create_experiment(db, who, project_id, data)


@router.get("/experiments/{experiment_id}", response_model=ExperimentOut)
def get_experiment(project_id: UUID, experiment_id: UUID, db: DB) -> ExperimentOut:
    return service.get_experiment(db, project_id, experiment_id)


@router.put("/experiments/{experiment_id}/protocol", response_model=ExperimentOut)
def update_protocol(project_id: UUID, experiment_id: UUID, data: ProtocolUpdate, db: DB, who: Who) -> ExperimentOut:
    return service.update_protocol(db, who, project_id, experiment_id, data)


@router.post("/experiments/{experiment_id}/transition", response_model=ExperimentTransitionOut)
def transition(
    project_id: UUID, experiment_id: UUID, data: ExperimentTransitionIn, db: DB, who: Who
) -> ExperimentTransitionOut:
    return service.transition(db, who, project_id, experiment_id, data)


@router.post("/experiments/{experiment_id}/readiness", response_model=GateEvaluationOut)
def evaluate_readiness(
    project_id: UUID, experiment_id: UUID, db: DB, who: Who, target: ExperimentState = ExperimentState.APPROVED
) -> GateEvaluationOut:
    return service.evaluate_readiness(db, who, project_id, experiment_id, target)


@router.get("/experiments/{experiment_id}/record", response_model=ExperimentRecordOut)
def experiment_record(project_id: UUID, experiment_id: UUID, db: DB) -> ExperimentRecordOut:
    return service.experiment_record(db, project_id, experiment_id)


@router.post("/experiments/{experiment_id}/human-impact", response_model=ImpactOut, status_code=status.HTTP_201_CREATED)
def assess_impact(project_id: UUID, experiment_id: UUID, data: ImpactIn, db: DB, who: Who) -> ImpactOut:
    return service.assess_impact(db, who, project_id, experiment_id, data)


@router.post(
    "/experiments/{experiment_id}/observations", response_model=ObservationOut, status_code=status.HTTP_201_CREATED
)
def record_observation(project_id: UUID, experiment_id: UUID, data: ObservationIn, db: DB, who: Who) -> ObservationOut:
    return service.record_observation(db, who, project_id, experiment_id, data)


@router.post("/experiments/{experiment_id}/results", response_model=ResultOut, status_code=status.HTTP_201_CREATED)
def record_result(project_id: UUID, experiment_id: UUID, data: ResultIn, db: DB, who: Who) -> ResultOut:
    return service.record_result(db, who, project_id, experiment_id, data)


@router.post(
    "/experiments/{experiment_id}/interpretations",
    response_model=InterpretationOut,
    status_code=status.HTTP_201_CREATED,
)
def record_interpretation(
    project_id: UUID, experiment_id: UUID, data: InterpretationIn, db: DB, who: Who
) -> InterpretationOut:
    return service.record_interpretation(db, who, project_id, experiment_id, data)
