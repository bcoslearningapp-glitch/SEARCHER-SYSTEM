"""Terminology and translation-integrity API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research_api.contracts.enums import LanguageCode, TermStatus
from research_api.modules.governance_audit.schemas import Actor


class Translations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ar: str | None = None
    en: str | None = None
    fr: str | None = None


class AlternativeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: LanguageCode
    text: str = Field(min_length=1)
    note: str | None = None


class TermIn(BaseModel):
    term: str = Field(min_length=1)
    original_language: LanguageCode
    domain: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    translations: Translations = Field(default_factory=Translations)
    alternatives: list[AlternativeIn] = Field(default_factory=list)
    retain_original: bool = False
    source_authority: str | None = None

    @model_validator(mode="after")
    def _original_form(self) -> TermIn:
        # The canonical term is its own form in the original language.
        if getattr(self.translations, self.original_language.value) is None:
            setattr(self.translations, self.original_language.value, self.term)
        return self


class TermRevision(TermIn):
    change_reason: str = Field(min_length=1)


class TermDecision(BaseModel):
    reason: str | None = None


class TermOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    series_id: UUID
    version_number: int
    supersedes_id: UUID | None
    term: str
    original_language: LanguageCode
    domain: str
    definition: str
    translations: Translations
    alternatives: list[AlternativeIn]
    retain_original: bool
    source_authority: str | None
    status: TermStatus
    change_reason: str | None
    provenance: dict[str, Any]
    approved_by: Actor | None
    approved_at: datetime | None
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        data = self.model_dump(
            mode="json", exclude_none=True, exclude={"change_reason", "approved_by", "approved_at", "created_at"}
        )
        data["alternatives"] = [{k: v for k, v in a.items() if v is not None} for a in data["alternatives"]]
        return data


class TranslationCheckIn(BaseModel):
    source_text: str = Field(min_length=1, max_length=20000)
    source_language: LanguageCode
    translated_text: str = Field(min_length=1, max_length=20000)
    target_language: LanguageCode
    domain: str | None = None


class StrengthProfileOut(BaseModel):
    relation: str
    certainty: str
    scope: str
    markers: dict[str, list[str]]


class DriftOut(BaseModel):
    axis: str
    direction: str
    source_level: str
    translation_level: str
    message: str


class TermFinding(BaseModel):
    term_id: UUID
    term: str
    source_form: str
    expected: list[str]
    found: bool
    message: str


class TranslationCheckOut(BaseModel):
    """A deterministic screen for a person to review; a clean result is not proof of fidelity."""

    source_profile: StrengthProfileOut
    translation_profile: StrengthProfileOut
    strength_drift: list[DriftOut]
    terminology: list[TermFinding]
    passed: bool
