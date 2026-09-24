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
    EvidenceStrength,
    OpenQuestionStatus,
    ResearchQuestionType,
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
