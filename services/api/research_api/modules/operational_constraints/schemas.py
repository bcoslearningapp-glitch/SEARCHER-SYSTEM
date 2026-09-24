"""Schemas for operational constraints and the combined target standing view."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from research_api.contracts.enums import ConstraintKind, EvidenceTargetType, OperationalConstraintState
from research_api.modules.reference_governance.schemas import ReferenceStanding


class ConstraintIn(BaseModel):
    target_type: EvidenceTargetType
    target_id: UUID
    kind: ConstraintKind
    state: OperationalConstraintState
    description: str = Field(min_length=1)
    jurisdiction: str | None = None
    source_reference: str | None = None
    required_change: str | None = Field(
        default=None, description="Lawful alternative, approval or policy change needed"
    )


class ResolveIn(BaseModel):
    resolution: str = Field(min_length=1)


class ConstraintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    target_type: EvidenceTargetType
    target_id: UUID
    kind: ConstraintKind
    state: OperationalConstraintState
    description: str
    jurisdiction: str | None
    source_reference: str | None
    required_change: str | None
    resolved_at: datetime | None
    resolution: str | None

    def to_contract(self) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude_none=True, exclude={"resolved_at", "resolution"})
        data["resolved"] = self.resolved_at is not None
        return data


class OperationalStanding(BaseModel):
    constraints: list[ConstraintOut]
    execution_ready: bool
    blocking: list[ConstraintOut]
    researchable: bool = Field(
        default=True, description="Research may continue even when current execution is not allowed (Core §74.27)"
    )


class TargetStanding(BaseModel):
    """Reference standing and operational reality side by side, never merged (Core §5, §51)."""

    target_type: EvidenceTargetType
    target_id: UUID
    reference: ReferenceStanding
    operational: OperationalStanding
    summary: str
