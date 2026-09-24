"""API schemas for hypotheses and mechanisms."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from research_api.contracts.enums import (
    HypothesisEpistemicState,
    HypothesisLifecycleState,
    MechanismStatus,
)
from research_api.modules.governance_audit.schemas import Actor, GateEvaluationOut


class HypothesisContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=1)
    context: str = ""
    expected_outcome: str = ""
    proposed_mechanism: str = ""
    assumptions: list[str] = Field(default_factory=list)
    boundary_conditions: list[str] = Field(default_factory=list)
    falsification_conditions: list[str] = Field(default_factory=list)


class HypothesisIn(BaseModel):
    content: HypothesisContent
    lifecycle_state: HypothesisLifecycleState = HypothesisLifecycleState.IDEA


class ReviseIn(BaseModel):
    content: HypothesisContent
    change_reason: str = Field(min_length=1)


class TransitionIn(BaseModel):
    target: HypothesisLifecycleState
    reason: str = Field(min_length=1)


class AssessIn(BaseModel):
    epistemic_state: HypothesisEpistemicState
    reason: str = Field(min_length=1)


class VersionOut(BaseModel):
    id: UUID
    hypothesis_id: UUID
    version_number: int
    content: HypothesisContent
    lifecycle_state: HypothesisLifecycleState
    epistemic_state: HypothesisEpistemicState
    change_reason: str
    created_at: datetime
    actor: Actor

    def to_contract(self) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude_none=True)
        data["content"] = {k: v for k, v in data["content"].items() if v not in ("", [])}
        return data


class HypothesisOut(BaseModel):
    id: UUID
    project_id: UUID
    current_version: int
    lifecycle_state: HypothesisLifecycleState
    epistemic_state: HypothesisEpistemicState
    content: HypothesisContent
    competing_hypothesis_ids: list[UUID]
    mechanism_ids: list[UUID]
    suggested_epistemic_state: HypothesisEpistemicState
    counter_evidence_search_complete: bool
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json",
            exclude_none=True,
            include={
                "id",
                "project_id",
                "current_version",
                "lifecycle_state",
                "epistemic_state",
                "competing_hypothesis_ids",
                "mechanism_ids",
                "provenance",
            },
        )


class TransitionOut(BaseModel):
    hypothesis: HypothesisOut
    gate: GateEvaluationOut


class CompeteIn(BaseModel):
    other_hypothesis_id: UUID
    note: str | None = None


class MechanismIn(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)


class MechanismUpdate(BaseModel):
    status: MechanismStatus
    reason: str = Field(min_length=1)


class MechanismOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    description: str
    status: MechanismStatus
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"created_at"})


class LinkMechanismIn(BaseModel):
    mechanism_id: UUID
