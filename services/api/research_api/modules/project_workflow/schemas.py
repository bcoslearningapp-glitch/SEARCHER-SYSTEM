"""API schemas for projects, Research State, notes and Problem Frames."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from research_api.contracts.enums import (
    ClosureType,
    LanguageCode,
    ProblemFrameStatus,
    ProjectInputType,
    ProjectStatus,
    ResearchMode,
    RiskLevel,
    SensitivityLevel,
)
from research_api.modules.governance_audit.schemas import Actor, AIActionRecord, VersionContext

StrList = list[str]


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    initial_input: str = Field(min_length=1)
    input_type: ProjectInputType
    sensitivity: SensitivityLevel = SensitivityLevel.NORMAL
    risk_level: RiskLevel = RiskLevel.L1_EXPLORATORY
    primary_language: LanguageCode = LanguageCode.EN


class ProjectUpdate(BaseModel):
    """Researcher corrections (FR-PROJ-002). Status/mode change through dedicated actions."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    sensitivity: SensitivityLevel | None = None
    risk_level: RiskLevel | None = None
    primary_language: LanguageCode | None = None
    reason: str | None = None


class TransitionRequest(BaseModel):
    target: ProjectStatus
    reason: str | None = None


class ModeRequest(BaseModel):
    mode: ResearchMode
    reason: str | None = None


class ForkRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    reason: str | None = None


class CloseRequest(BaseModel):
    """Closure record (FR-CLOSE-002). The human closes; the system only proposes readiness."""

    closure_type: ClosureType
    resolved: StrList = Field(min_length=1)
    unresolved: StrList = Field(default_factory=list)
    confidence_scope: str = Field(min_length=1)
    knowledge_promoted: StrList = Field(default_factory=list)
    open_questions: StrList = Field(default_factory=list)
    limitations: StrList = Field(default_factory=list)
    reopen_triggers: StrList = Field(default_factory=list)
    acknowledge_reservations: bool = Field(default=False, exclude=True)
    override_reason: str | None = Field(default=None, exclude=True, description="Why close despite the gate")


class ReopenRequest(BaseModel):
    trigger: str = Field(min_length=1, description="Why the project reopens (Core §67)")


class ProjectOut(BaseModel):
    id: UUID
    title: str
    initial_input: str
    input_type: ProjectInputType
    sensitivity: SensitivityLevel
    risk_level: RiskLevel
    status: ProjectStatus
    research_mode: ResearchMode
    primary_language: LanguageCode
    forked_from_project_id: UUID | None
    versions: VersionContext
    owner: Actor
    created_at: datetime
    updated_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ResearchStateUpdate(BaseModel):
    current_question: str | None = None
    established_findings: StrList | None = None
    unresolved_items: StrList | None = None
    reservations: StrList | None = None
    blockers: StrList | None = None
    next_action: str | None = None
    next_action_reason: str | None = None


class ResearchStateOut(BaseModel):
    project_id: UUID
    current_question: str | None
    current_mode: ResearchMode
    established_findings: StrList
    unresolved_items: StrList
    active_hypothesis_ids: list[UUID]
    reservations: StrList
    blockers: StrList
    pending_decision_ids: list[UUID]
    next_action: str | None
    next_action_reason: str | None
    updated_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ClosureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    closure_type: ClosureType
    record: dict[str, Any]
    closed_by_id: str
    closed_at: datetime
    reopened_at: datetime | None
    reopen_trigger: str | None
    gate_evaluation_id: UUID | None = None
    approval_id: UUID | None = None


# --- Scratch notes (FR-SCRATCH-001..003) ---


class NoteCreate(BaseModel):
    body: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    body: str = Field(min_length=1)


class NoteCaptureTarget(BaseModel):
    """Explicit capture of a note into formal state. Only researcher-initiated in Phase 1."""

    target: str = Field(pattern="^(current_question|unresolved_item|established_finding)$")


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    body: str
    author_id: str
    captured_as: str | None
    captured_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Problem Frame (FR-FRAME-005..007) ---


class ProblemFrameContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    central_issue: str = ""
    current_state: str = ""
    desired_state: str = ""
    gap: str = ""
    current_explanations: StrList = Field(default_factory=list)
    initial_hypotheses: StrList = Field(default_factory=list)
    context: str = ""
    constraints: StrList = Field(default_factory=list)
    known: StrList = Field(default_factory=list)
    unknowns: StrList = Field(default_factory=list)
    research_questions: StrList = Field(default_factory=list)
    reference_review_points: StrList = Field(default_factory=list)
    readiness: str = ""


class ProblemFrameDraftIn(BaseModel):
    content: ProblemFrameContent


class ProblemFrameApproveIn(BaseModel):
    reason: str | None = None
    acknowledge_reservations: bool = Field(
        default=False,
        description="Required when the Framing Gate returns NEEDS_HUMAN_DECISION; records an override.",
    )


class ProblemFrameOut(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    status: ProblemFrameStatus
    content: ProblemFrameContent
    provenance: dict[str, Any]
    approval_id: UUID | None
    supersedes_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None

    def to_contract(self) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude_none=True, exclude={"updated_at"})
        data["content"] = {k: v for k, v in data["content"].items() if v not in ("", [])}
        return data


class DraftByAI(BaseModel):
    """Internal: an AI-proposed draft always carries provenance (Core §71)."""

    content: ProblemFrameContent
    ai_action: AIActionRecord
