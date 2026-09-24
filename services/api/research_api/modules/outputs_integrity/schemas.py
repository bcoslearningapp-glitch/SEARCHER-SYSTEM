"""Output API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research_api.contracts.enums import (
    LanguageCode,
    OutputBlockKind,
    OutputMode,
    OutputType,
    OutputVersionStatus,
    QuoteSourceKind,
)
from research_api.modules.governance_audit.schemas import Actor, ApprovalOut

# Output types written about one entity rather than the whole project.
SUBJECT_TYPES = {
    OutputType.HYPOTHESIS_DOSSIER: "Hypothesis",
    OutputType.EXPERIMENT_PROTOCOL: "Experiment",
    OutputType.LEARNING_REVIEW: "Experiment",
}


class Trace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str = Field(max_length=60)
    entity_id: UUID


class Quote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_kind: QuoteSourceKind
    excerpt_id: UUID | None = None
    quran_ref: str | None = Field(default=None, pattern=r"^[0-9]{1,3}:[0-9]{1,3}(-[0-9]{1,3})?$")
    hadith_record_id: UUID | None = None
    text: str = Field(min_length=1)
    language: str | None = None

    @model_validator(mode="after")
    def _reference_present(self) -> Quote:
        needed = {
            QuoteSourceKind.EXCERPT: self.excerpt_id,
            QuoteSourceKind.QURAN: self.quran_ref,
            QuoteSourceKind.HADITH: self.hadith_record_id,
        }[self.source_kind]
        if needed is None:
            raise ValueError(f"a {self.source_kind.value} quote names its source")
        return self


class Block(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: OutputBlockKind
    text: str = ""
    level: int | None = Field(default=None, ge=1, le=4)
    items: list[str] | None = None
    label: str | None = None
    trace: list[Trace] = Field(default_factory=list)
    quote: Quote | None = None

    @model_validator(mode="after")
    def _kind_rules(self) -> Block:
        if self.kind is OutputBlockKind.CLAIM and not self.trace:
            raise ValueError("a CLAIM block must trace to the entities it rests on (FR-OUT-004)")
        if self.kind is OutputBlockKind.QUOTE and self.quote is None:
            raise ValueError("a QUOTE block carries its protected quote")
        return self


class OutputIn(BaseModel):
    output_type: OutputType
    title: str = Field(min_length=1)
    language: LanguageCode = LanguageCode.EN
    mode: OutputMode = OutputMode.REFERENCED
    subject_id: UUID | None = None

    @model_validator(mode="after")
    def _subject(self) -> OutputIn:
        if self.output_type in SUBJECT_TYPES and self.subject_id is None:
            raise ValueError(f"{self.output_type.value} is written about one {SUBJECT_TYPES[self.output_type]}")
        return self


class ReviseIn(BaseModel):
    blocks: list[Block] = Field(min_length=1)
    change_reason: str = Field(min_length=1)


class SettingsIn(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    mode: OutputMode | None = None


class ApproveIn(BaseModel):
    reason: str | None = None


class VersionOut(BaseModel):
    id: UUID
    output_id: UUID
    version_number: int
    status: OutputVersionStatus
    blocks: list[Block]
    change_reason: str | None
    approval_id: UUID | None
    created_by: Actor
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude_none=True)
        return data


class OutputOut(BaseModel):
    id: UUID
    project_id: UUID
    output_type: OutputType
    title: str
    language: LanguageCode
    mode: OutputMode
    subject_type: str | None
    subject_id: UUID | None
    current_version: int
    provenance: dict[str, Any]
    created_at: datetime
    latest: VersionOut

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"created_at", "latest"})


class ApproveOut(BaseModel):
    version: VersionOut
    approval: ApprovalOut
