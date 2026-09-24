"""API schemas for claims, assumptions and open questions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from research_api.contracts.enums import (
    AssumptionOrigin,
    AssumptionStatus,
    ClaimType,
    ClaimWorkflowState,
    Criticality,
    EvidenceRole,
    EvidenceStatus,
    EvidenceStrength,
    EvidenceTargetType,
    LineageRelation,
    OpenQuestionStatus,
    ResearchOutcomeKind,
    ResearchQuestionType,
    ResearchTrack,
    StatementOrigin,
    SufficiencyResult,
)


class ClaimIn(BaseModel):
    statement: str = Field(min_length=1)
    claim_type: ClaimType
    important: bool = False


class ClaimUpdate(BaseModel):
    workflow_state: ClaimWorkflowState | None = None
    important: bool | None = None
    reason: str | None = None


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    statement: str
    claim_type: ClaimType
    statement_origin: StatementOrigin
    workflow_state: ClaimWorkflowState
    epistemic_strength: EvidenceStrength
    important: bool
    provenance: dict[str, Any]
    source_note_id: UUID | None
    created_at: datetime
    updated_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"source_note_id", "created_at", "updated_at"})


class AssumptionIn(BaseModel):
    statement: str = Field(min_length=1)
    criticality: Criticality = Criticality.MEDIUM
    origin: Literal["EXPLICIT", "SOURCE_DERIVED"] = "EXPLICIT"
    claim_id: UUID | None = None


class AssumptionReview(BaseModel):
    """Human review of an assumption (FR-CLAIM-003)."""

    status: Literal["CONFIRMED", "REJECTED", "RECLASSIFIED"]
    reclassify_as: Literal["EXPLICIT", "SOURCE_DERIVED"] | None = None
    criticality: Criticality | None = None
    note: str | None = None


class AssumptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    statement: str
    origin: AssumptionOrigin
    criticality: Criticality
    status: AssumptionStatus
    claim_id: UUID | None
    provenance: dict[str, Any]
    review_note: str | None
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"review_note", "created_at"})


class OpenQuestionIn(BaseModel):
    question: str = Field(min_length=1)
    question_type: ResearchQuestionType


class OpenQuestionClose(BaseModel):
    status: Literal["ANSWERED", "CLOSED_UNANSWERED"]
    conclusion: SufficiencyResult


class OpenQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    question: str
    question_type: ResearchQuestionType
    status: OpenQuestionStatus
    conclusion: SufficiencyResult | None
    created_at: datetime


class CaptureIn(BaseModel):
    """Capture a scratch note into a formal entity (FR-CLAIM-005, FR-SCRATCH-002)."""

    as_: Literal["claim", "assumption", "open_question"] = Field(alias="as")
    claim_type: ClaimType | None = None
    question_type: ResearchQuestionType | None = None
    criticality: Criticality = Criticality.MEDIUM


# --- evidence (Core §32-36) ---


class EvidenceIn(BaseModel):
    target_type: EvidenceTargetType
    target_id: UUID
    role: EvidenceRole
    finding: str = Field(min_length=1, description="What the source passage shows, in the researcher's words")
    excerpt_id: UUID
    track: ResearchTrack | None = None


class AssessmentIn(BaseModel):
    """Human assessment: accept with qualitative assessment, or reject (FR-EVID-003)."""

    decision: Literal["ACCEPT", "REJECT"]
    strength: EvidenceStrength | None = None
    quality: str | None = None
    relevance: str | None = None
    context_fit: str | None = None
    directness: str | None = None
    limitations: str | None = None
    temporal_relevance: str | None = None
    reason: str | None = None


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    target_type: EvidenceTargetType
    target_id: UUID
    role: EvidenceRole
    status: EvidenceStatus
    finding: str
    excerpt_id: UUID
    track: ResearchTrack | None
    assessment: dict[str, Any] | None
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"created_at"})


class LineageIn(BaseModel):
    from_work_id: UUID
    relation: LineageRelation
    to_work_id: UUID
    note: str | None = None


class LineageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_work_id: UUID
    relation: LineageRelation
    to_work_id: UUID
    note: str | None


class TrackRunIn(BaseModel):
    target_type: EvidenceTargetType
    target_id: UUID
    track: ResearchTrack
    outcome: ResearchOutcomeKind
    scope: str = Field(min_length=1, description="What was searched: libraries, databases, languages")
    queries: list[str] = Field(default_factory=list)


class TrackRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_type: EvidenceTargetType
    target_id: UUID
    track: ResearchTrack
    outcome: ResearchOutcomeKind
    scope: str
    queries: list[str]
    created_at: datetime


class TrackStatus(BaseModel):
    track: ResearchTrack
    searched: bool
    last_outcome: ResearchOutcomeKind | None
    # A failed search is not evidence absence (Core §72).
    execution_failed: bool


class EvidenceMap(BaseModel):
    target_type: EvidenceTargetType
    target_id: UUID
    by_role: dict[str, list[EvidenceOut]]
    candidates: list[EvidenceOut]
    support_origins: int
    contra_origins: int
    shared_origin_groups: list[list[UUID]]
    meaningful_conflict: bool
    suggested_strength: EvidenceStrength
    tracks: list[TrackStatus]
    counter_evidence_search_complete: bool
