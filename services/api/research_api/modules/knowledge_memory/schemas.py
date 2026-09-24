"""Knowledge memory API schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research_api.contracts.enums import (
    EvidenceStrength,
    KnowledgeLifecycleStage,
    KnowledgeStatus,
    TemporalProfile,
    TransferabilityState,
)
from research_api.modules.governance_audit.schemas import Actor, GateEvaluationOut

BASIS_TYPES = Literal[
    "ExperimentInterpretation",
    "LearningReview",
    "CLAIM",
    "HYPOTHESIS",
    "MECHANISM",
    "DESIGN_CONCEPT",
    "DESIGN_HYPOTHESIS",
]


class BasisIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: BASIS_TYPES
    entity_id: UUID
    context: str | None = None
    note: str | None = None


class TemporalIn(BaseModel):
    temporal_profile: TemporalProfile = TemporalProfile.SLOW_CHANGING
    valid_from: date | None = None
    revalidation_interval_days: int | None = Field(default=None, ge=1)
    source_version: str | None = None

    @model_validator(mode="after")
    def _policy_for_time_sensitive(self) -> TemporalIn:
        volatile = {TemporalProfile.DYNAMIC, TemporalProfile.HIGHLY_VOLATILE}
        if self.temporal_profile in volatile and self.revalidation_interval_days is None:
            raise ValueError("time-sensitive knowledge needs a revalidation interval (FR-TIME-002)")
        return self


class KnowledgeIn(TemporalIn):
    statement: str = Field(min_length=1)
    scope: str = ""
    contexts: list[str] = Field(default_factory=list)
    evidence_basis: list[BasisIn] = Field(min_length=1)
    contrary_evidence: list[BasisIn] = Field(default_factory=list)
    contrary_evidence_searched: bool = False
    confidence: EvidenceStrength = EvidenceStrength.PROMISING


class KnowledgeRevision(KnowledgeIn):
    reason: str = Field(min_length=1)


class PromoteIn(BaseModel):
    target: KnowledgeLifecycleStage
    reason: str | None = None
    acknowledge_reservations: bool = False


class StandingIn(BaseModel):
    """Downgrade, contest, suspend, reinstate or revalidate (FR-KNOW-004)."""

    action: Literal["DOWNGRADE", "CONTEST", "SUSPEND", "REINSTATE", "REVALIDATE"]
    reason: str = Field(min_length=1)
    target_stage: KnowledgeLifecycleStage | None = None
    source_version: str | None = None


class VersionOut(BaseModel):
    version_number: int
    change: str
    reason: str
    stage: KnowledgeLifecycleStage
    status: KnowledgeStatus
    gate_evaluation_id: UUID | None
    actor: Actor
    created_at: datetime


class KnowledgeOut(BaseModel):
    id: UUID
    project_id: UUID
    current_version: int
    statement: str
    stage: KnowledgeLifecycleStage
    status: KnowledgeStatus
    effective_status: KnowledgeStatus
    revalidation_due: bool
    scope: str
    contexts: list[str]
    evidence_basis: list[BasisIn]
    contrary_evidence: list[BasisIn]
    contrary_evidence_searched: bool
    confidence: EvidenceStrength
    temporal_profile: TemporalProfile
    valid_from: date | None
    last_verified_at: datetime | None
    revalidation_interval_days: int | None
    source_version: str | None
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json", exclude_none=True, exclude={"effective_status", "revalidation_due", "created_at"}
        )


class PromoteOut(BaseModel):
    item: KnowledgeOut
    gate: GateEvaluationOut


class ReuseIn(BaseModel):
    target_project_id: UUID
    transferability: TransferabilityState
    rationale: str = Field(min_length=1)
    differences: str | None = None


class ReuseOut(BaseModel):
    id: UUID
    knowledge_item_id: UUID
    knowledge_version: int
    target_project_id: UUID
    transferability: TransferabilityState
    rationale: str
    differences: str | None
    assessed_by: Actor
    created_at: datetime
    statement: str
    source_project_id: UUID
    stage: KnowledgeLifecycleStage
    effective_status: KnowledgeStatus
    direct_evidence: Literal[False] = False
    label: str

    def to_contract(self) -> dict[str, Any]:
        keep = {
            "id",
            "knowledge_item_id",
            "knowledge_version",
            "target_project_id",
            "transferability",
            "rationale",
            "differences",
            "assessed_by",
            "created_at",
        }
        return self.model_dump(mode="json", exclude_none=True, include=keep)
