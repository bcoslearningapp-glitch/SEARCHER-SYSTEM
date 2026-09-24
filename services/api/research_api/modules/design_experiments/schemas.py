"""Design lab API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from research_api.contracts.enums import (
    DesignConceptStatus,
    DesignOrigin,
    DesignRequirementBasis,
    DesignRequirementStatus,
    RejectionGround,
    RequirementCoverage,
    RequirementPriority,
)
from research_api.modules.governance_audit.schemas import ApprovalOut, GateEvaluationOut


class TraceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    basis: DesignRequirementBasis
    entity_type: str | None = Field(default=None, max_length=60)
    entity_id: UUID | None = None
    note: str | None = None


class RequirementIn(BaseModel):
    statement: str = Field(min_length=1)
    priority: RequirementPriority = RequirementPriority.MUST
    traces: list[TraceIn] = Field(min_length=1, description="What the requirement is derived from (FR-DESIGN-002)")


class RequirementRevision(RequirementIn):
    change_reason: str = Field(min_length=1)


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    series_id: UUID
    version_number: int
    supersedes_id: UUID | None
    statement: str
    priority: RequirementPriority
    traces: list[TraceIn]
    status: DesignRequirementStatus
    change_reason: str | None
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"change_reason", "created_at"})


class ConceptIn(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    origin: DesignOrigin = DesignOrigin.RESEARCHER
    origin_reference: str | None = None
    hypothesis_ids: list[UUID] = Field(default_factory=list)
    mechanism_ids: list[UUID] = Field(default_factory=list)
    derived_from_concept_ids: list[UUID] = Field(default_factory=list)


class CoverageIn(BaseModel):
    requirement_id: UUID
    coverage: RequirementCoverage
    note: str | None = None


class CoverageOut(BaseModel):
    requirement_id: UUID
    requirement_series_id: UUID
    coverage: RequirementCoverage
    note: str | None
    stale: bool


class RejectIn(BaseModel):
    ground: RejectionGround
    reason: str = Field(min_length=1)
    reusable_mechanism_ids: list[UUID] = Field(default_factory=list)


class SelectIn(BaseModel):
    reason: str | None = None
    acknowledge_reservations: bool = False


class RequirementStatusIn(BaseModel):
    reason: str | None = None


class WithdrawIn(BaseModel):
    reason: str = Field(min_length=1)


class StatusIn(BaseModel):
    target: Literal["UNDER_REVIEW", "WITHDRAWN"]
    reason: str | None = None


class ConceptOut(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    origin: DesignOrigin
    origin_reference: str | None
    status: DesignConceptStatus
    hypothesis_ids: list[UUID]
    mechanism_ids: list[UUID]
    derived_from_concept_ids: list[UUID]
    coverage: list[CoverageOut]
    rejection: dict[str, Any] | None
    selection: dict[str, Any] | None
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude_none=True, exclude={"selection", "created_at"})
        data["coverage"] = [
            {k: v for k, v in c.items() if k in {"requirement_id", "coverage", "note"} and v is not None}
            for c in data["coverage"]
        ]
        if "rejection" in data:
            data["rejection"] = {
                k: v for k, v in data["rejection"].items() if k in {"ground", "reason", "reusable_mechanism_ids"}
            }
        return data


class SelectOut(BaseModel):
    concept: ConceptOut
    gate: GateEvaluationOut
    approval: ApprovalOut
