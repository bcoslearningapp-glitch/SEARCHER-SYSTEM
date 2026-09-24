"""Design hypothesis, experiment, human-impact and observation/result/interpretation API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research_api.contracts.enums import (
    ExperimentState,
    HumanImpactDimension,
    HumanImpactFinding,
    HypothesisEpistemicState,
    InterpretationOutcome,
)
from research_api.modules.governance_audit.schemas import Actor, ApprovalOut, GateEvaluationOut

CONTRACT_DROP = {"created_at", "updated_at"}


class DesignHypothesisContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intervention: str = Field(min_length=1)
    target_population: str = Field(min_length=1)
    context: str = Field(min_length=1)
    mechanism: str = Field(min_length=1)
    expected_outcome: str = Field(min_length=1)
    measurement_plan: str = Field(min_length=1)
    failure_conditions: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)


class DesignHypothesisIn(BaseModel):
    concept_id: UUID
    content: DesignHypothesisContent
    affects_people: bool


class DesignHypothesisRevision(BaseModel):
    content: DesignHypothesisContent
    change_reason: str = Field(min_length=1)


class DesignHypothesisAssess(BaseModel):
    epistemic_state: HypothesisEpistemicState
    reason: str = Field(min_length=1)


class DesignHypothesisOut(BaseModel):
    id: UUID
    project_id: UUID
    concept_id: UUID
    current_version: int
    content: DesignHypothesisContent
    affects_people: bool
    epistemic_state: HypothesisEpistemicState
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude=CONTRACT_DROP)


class ProtocolIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str = ""
    sample: str = ""
    duration: str = ""
    data_collected: str = ""
    analysis_plan: str = ""
    success_criteria: str = ""


class ExperimentIn(BaseModel):
    design_hypothesis_id: UUID
    title: str = Field(min_length=1)
    protocol: ProtocolIn = Field(default_factory=ProtocolIn)


class ProtocolUpdate(BaseModel):
    protocol: ProtocolIn
    reason: str = Field(min_length=1)


class ExperimentTransitionIn(BaseModel):
    target: ExperimentState
    reason: str | None = None
    acknowledge_reservations: bool = False

    @model_validator(mode="after")
    def _stops_need_reason(self) -> ExperimentTransitionIn:
        stops = {ExperimentState.PAUSED, ExperimentState.ABORTED, ExperimentState.INVALIDATED}
        if self.target in stops and not (self.reason and self.reason.strip()):
            raise ValueError(f"{self.target.value} needs a reason")
        return self


class TransitionRecord(BaseModel):
    from_state: ExperimentState
    to_state: ExperimentState
    reason: str | None
    gate_evaluation_id: UUID | None
    actor: Actor
    created_at: datetime


class ExperimentOut(BaseModel):
    id: UUID
    project_id: UUID
    design_hypothesis_id: UUID
    title: str
    protocol: ProtocolIn
    state: ExperimentState
    paused_from: ExperimentState | None
    affects_people: bool
    invalidation_reason: str | None
    approval_id: UUID | None
    provenance: dict[str, Any]
    transitions: list[TransitionRecord]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        data = self.model_dump(
            mode="json", exclude_none=True, exclude={"paused_from", "approval_id", "transitions", "created_at"}
        )
        data["protocol"] = {k: v for k, v in data["protocol"].items() if v}
        return data


class ExperimentTransitionOut(BaseModel):
    experiment: ExperimentOut
    gate: GateEvaluationOut | None
    approval: ApprovalOut | None


class ImpactIn(BaseModel):
    dimension: HumanImpactDimension
    finding: HumanImpactFinding
    note: str = Field(min_length=1)
    external_authority: str | None = None

    @model_validator(mode="after")
    def _authority_named(self) -> ImpactIn:
        if self.finding is HumanImpactFinding.REQUIRES_EXTERNAL_APPROVAL and not self.external_authority:
            raise ValueError("name the authority whose approval is required")
        return self


class ImpactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    dimension: HumanImpactDimension
    finding: HumanImpactFinding
    note: str
    external_authority: str | None
    operational_constraint_id: UUID | None
    assessed_by: Actor
    assessed_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ObservationIn(BaseModel):
    description: str = Field(min_length=1)
    measurements: dict[str, Any] | None = None
    observed_at: datetime


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    description: str
    measurements: dict[str, Any] | None
    observed_at: datetime
    recorded_by: Actor

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ResultIn(BaseModel):
    observation_ids: list[UUID] = Field(min_length=1)
    method: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    values: dict[str, Any] | None = None


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    observation_ids: list[UUID]
    method: str
    summary: str
    values: dict[str, Any] | None
    recorded_by: Actor

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class InterpretationIn(BaseModel):
    result_ids: list[UUID] = Field(min_length=1)
    outcome: InterpretationOutcome
    statement: str = Field(min_length=1)
    limitations: str | None = None


class InterpretationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    result_ids: list[UUID]
    outcome: InterpretationOutcome
    statement: str
    limitations: str | None
    interpreted_by: Actor

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class LearningReviewIn(BaseModel):
    learned: str = Field(min_length=1)
    hypothesis_effect: str = Field(min_length=1, description="What this means for the design hypothesis")
    surprises: str | None = None
    limitations: list[str] = Field(default_factory=list)
    validity_threats: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class LearningReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    learned: str
    hypothesis_effect: str
    surprises: str | None
    limitations: list[str]
    validity_threats: list[str]
    next_steps: list[str]
    reviewed_by: Actor
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ExperimentRecordOut(BaseModel):
    """Observation, result and interpretation kept as distinct lists (FR-EXP-003)."""

    human_impact: list[ImpactOut]
    observations: list[ObservationOut]
    results: list[ResultOut]
    interpretations: list[InterpretationOut]
    learning_reviews: list[LearningReviewOut]
