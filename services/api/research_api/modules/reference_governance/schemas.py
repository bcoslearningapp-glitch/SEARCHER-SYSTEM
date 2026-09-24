"""API schemas for the foundational library and reference review."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from research_api.contracts.enums import (
    ActorRole,
    Directness,
    EvidenceTargetType,
    FoundationalSourceStatus,
    QualityGateResult,
    ReferenceAnalyticalCategory,
    ReferenceAuthorityLayer,
    ReferenceJudgmentState,
    ReferenceReasoningLayer,
    ReservationType,
)
from research_api.modules.governance_audit.schemas import Actor, GateEvaluationOut


class FoundationalStageIn(BaseModel):
    work_id: UUID
    edition_version: str = Field(min_length=1)
    sha256: str = Field(pattern="^[a-f0-9]{64}$")


class ApproveIn(BaseModel):
    reason: str = Field(min_length=1)


class FoundationalOut(BaseModel):
    id: UUID
    work_id: UUID
    authority_layer: ReferenceAuthorityLayer
    edition_version: str
    status: FoundationalSourceStatus
    sha256: str
    dataset_summary: dict[str, Any]
    approved_by: Actor | None
    approved_at: datetime | None

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"dataset_summary"})


class AyahOut(BaseModel):
    surah_number: int
    surah_name: str
    ayah_number: int
    text: str
    source_id: UUID
    source_version: str
    source_sha256: str


class HadithIn(BaseModel):
    collection: str = Field(min_length=1)
    book: str | None = None
    chapter: str | None = None
    number: str = Field(min_length=1, max_length=40)
    numbering_scheme: str = Field(min_length=1, description="The edition whose numbering `number` follows")
    narrator: str | None = None
    exact_text: str = Field(min_length=1)
    location: str | None = None


class HadithOut(HadithIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    foundational_source_id: UUID


class ReviewIn(BaseModel):
    target_type: EvidenceTargetType
    target_id: UUID
    question: str = Field(min_length=1)
    analytical_category: ReferenceAnalyticalCategory


class EntryIn(BaseModel):
    layer: ReferenceReasoningLayer
    content: str | None = Field(
        default=None, description="Required except for SOURCE_TEXT, whose content is copied from the source"
    )
    source_excerpt_id: UUID | None = None
    quran_ref: str | None = Field(default=None, pattern=r"^[0-9]{1,3}:[0-9]{1,3}(-[0-9]{1,3})?$")
    hadith_record_id: UUID | None = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    review_id: UUID
    layer: ReferenceReasoningLayer
    content: str
    source_excerpt_id: UUID | None
    quran_ref: str | None
    hadith_record_id: UUID | None
    provenance: dict[str, Any]
    created_at: datetime


class Divergence(BaseModel):
    interpretation_a: str = Field(min_length=1)
    source_a: str | None = None
    interpretation_b: str = Field(min_length=1)
    source_b: str | None = None
    implications: str = Field(min_length=1)
    required_authority: ActorRole = ActorRole.CONSTITUTIONAL_AUTHORITY


class JudgmentIn(BaseModel):
    state: ReferenceJudgmentState
    directness: Directness
    reservation_type: ReservationType | None = None
    divergence: Divergence | None = None
    rationale: str = Field(min_length=1)


class JudgmentOut(BaseModel):
    id: UUID
    review_id: UUID
    state: ReferenceJudgmentState
    directness: Directness
    reservation_type: ReservationType | None
    divergence: Divergence | None
    rationale: str
    judged_by: Actor
    decision_id: UUID | None
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"decision_id"})


class ReviewOut(BaseModel):
    id: UUID
    project_id: UUID
    target_type: EvidenceTargetType
    target_id: UUID
    question: str
    analytical_category: ReferenceAnalyticalCategory
    entries: list[EntryOut]
    judgments: list[JudgmentOut]
    current_judgment: JudgmentOut | None
    created_at: datetime


class ReferenceStanding(BaseModel):
    result: QualityGateResult
    findings: list[dict[str, Any]]
    latest_judgments: list[JudgmentOut]
    gate: GateEvaluationOut | None = None
