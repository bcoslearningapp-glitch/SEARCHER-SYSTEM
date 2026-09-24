"""Validated inputs/outputs for the audit framework, aligned with event.schema.json."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from research_api.contracts.enums import (
    ActorKind,
    ActorRole,
    ApprovalOutcome,
    DecisionStatus,
    MethodologyPathStatus,
    QualityGateResult,
    QualityGateType,
    RiskLevel,
)

_ACTION = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
_EVENT_TYPE = re.compile(r"^[A-Z][A-Za-z]+$")


class Actor(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ActorKind
    id: str = Field(min_length=1, max_length=200)
    role: ActorRole | None = None


class AIActionRecord(BaseModel):
    """Reproducibility metadata for a material AI action (Core §71, PRD §53)."""

    model_config = ConfigDict(frozen=True)

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    supplied_entity_ids: list[UUID] = Field(default_factory=list)
    task_id: str | None = None
    timestamp: datetime


class _EventInput(BaseModel):
    project_id: UUID | None = None
    entity_type: str | None = Field(default=None, max_length=100)
    entity_id: UUID | None = None
    actor: Actor


class AuditEntry(_EventInput):
    action: str = Field(description="dotted verb, e.g. problem_frame.approve")
    previous_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None
    reason: str | None = None
    ai_action: AIActionRecord | None = None

    @field_validator("action")
    @classmethod
    def _action_format(cls, value: str) -> str:
        if not _ACTION.match(value):
            raise ValueError("action must be a dotted lower_snake verb such as 'problem_frame.approve'")
        return value

    @model_validator(mode="after")
    def _ai_actions_carry_provenance(self) -> Self:
        if self.actor.kind is ActorKind.AI and self.ai_action is None:
            raise ValueError("AI-actor audit entries must include ai_action provenance (Core §71)")
        return self


class ResearchEventEntry(_EventInput):
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def _event_type_format(cls, value: str) -> str:
        if not _EVENT_TYPE.match(value):
            raise ValueError("event_type must be PascalCase, e.g. 'ProblemFrameApproved'")
        return value


class VersionContext(BaseModel):
    core_schema_version: str
    methodology_version: str
    constitution_version: str


class AuditEventOut(BaseModel):
    id: UUID
    project_id: UUID | None
    action: str
    entity_type: str | None
    entity_id: UUID | None
    occurred_at: datetime
    actor: Actor
    versions: VersionContext
    previous_state: dict[str, Any] | None
    new_state: dict[str, Any] | None
    reason: str | None
    ai_action: AIActionRecord | None

    def to_contract(self) -> dict[str, Any]:
        """Serialize to the canonical contract shape (event.schema.json#AuditEvent)."""
        return self.model_dump(mode="json", exclude_none=True)


# --- Approvals, gates, decisions ---


class GateFinding(BaseModel):
    code: str
    severity: QualityGateResult
    message: str


class GateEvaluationOut(BaseModel):
    id: UUID
    project_id: UUID | None
    gate: QualityGateType
    subject_type: str | None
    subject_id: UUID | None
    result: QualityGateResult
    risk_level: RiskLevel
    findings: list[GateFinding]
    evaluated_at: datetime
    methodology_version: str


class ApprovalOut(BaseModel):
    id: UUID
    project_id: UUID
    subject_type: str
    subject_id: UUID
    outcome: ApprovalOutcome
    approved_by: Actor
    reason: str | None
    methodology_path: MethodologyPathStatus
    gate_evaluation_id: UUID | None
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class AIRecommendation(BaseModel):
    option: str
    rationale: str
    ai_action: AIActionRecord


class DecisionCreate(BaseModel):
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2)
    rationale: str | None = None
    required_role: ActorRole = ActorRole.RESEARCHER
    blocking: bool = False
    subject_type: str | None = None
    subject_id: UUID | None = None


class DecisionResolve(BaseModel):
    final_decision: str = Field(min_length=1)
    human_justification: str = Field(min_length=1)
    incomplete_evidence: bool = Field(
        default=False,
        description="Degraded Decision Mode: mark DECISION_UNDER_INCOMPLETE_EVIDENCE (FR-DEGRADED-002).",
    )
    unverified: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    later_review: str | None = None


class DecisionOut(BaseModel):
    id: UUID
    project_id: UUID
    question: str
    options: list[str]
    ai_recommendation: AIRecommendation | None
    rationale: str | None
    required_role: ActorRole
    blocking: bool
    status: DecisionStatus
    subject_type: str | None
    subject_id: UUID | None
    final_decision: str | None
    human_justification: str | None
    methodology_path: MethodologyPathStatus | None
    decided_by: Actor | None
    decided_at: datetime | None
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"subject_type", "subject_id", "created_at"})
