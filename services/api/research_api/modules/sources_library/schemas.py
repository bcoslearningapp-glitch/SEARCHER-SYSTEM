"""API schemas for the source library and Hybrid Source Access."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from research_api.contracts.enums import (
    AccessResponseForm,
    IngestionStatus,
    Priority,
    ReferenceAuthorityLayer,
    SourceAccessMode,
    SourceAccessRequestStatus,
    SourceAssetKind,
    SourceLeadOrigin,
    SourceLeadState,
    SourceVerificationState,
    TextOrigin,
)


class Identifier(BaseModel):
    scheme: Literal["ISBN", "DOI", "ISSN", "URL", "OCLC", "LCCN", "ARXIV", "PMID", "OTHER"]
    value: str = Field(min_length=1)


class WorkIn(BaseModel):
    title: str = Field(min_length=1)
    authors: list[str] = Field(default_factory=list)
    original_language: str | None = None
    authority_layer: ReferenceAuthorityLayer = ReferenceAuthorityLayer.SCIENTIFIC_EXPERIMENTAL
    identifiers: list[Identifier] = Field(default_factory=list)


class EditionIn(BaseModel):
    edition_label: str | None = None
    language: str | None = None
    translator: str | None = None
    publisher: str | None = None
    published_date: str | None = None
    identifiers: list[Identifier] = Field(default_factory=list)
    license_note: str | None = None
    portable_asset_allowed: bool = False


class HoldingIn(BaseModel):
    """A non-digital holding recorded at catalog time, e.g. the researcher's physical copy."""

    access_mode: Literal["PHYSICAL", "RESTRICTED", "RESEARCHER_MEDIATED"]
    note: str | None = None


class CatalogIn(BaseModel):
    work: WorkIn
    edition: EditionIn = Field(default_factory=EditionIn)
    holding: HoldingIn | None = None
    project_id: UUID | None = None


class ReverifyIn(BaseModel):
    verification_state: SourceVerificationState
    method: str = Field(min_length=1, description="How the content was verified (Core §25 ReverificationEvent)")
    reason: str | None = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    edition_id: UUID
    kind: SourceAssetKind
    access_mode: SourceAccessMode
    available_in_environment: bool
    sha256: str | None
    media_type: str | None
    byte_size: int | None
    original_filename: str | None
    text_origin: TextOrigin | None
    holding_note: str | None
    ingestion_status: IngestionStatus
    ingestion_job_id: UUID | None
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"original_filename", "holding_note", "ingestion_status", "ingestion_job_id", "created_at"},
        )


class EditionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_id: UUID
    edition_label: str | None
    language: str | None
    translator: str | None
    publisher: str | None
    published_date: str | None
    identifiers: list[Identifier]
    verification_state: SourceVerificationState
    license_note: str | None
    portable_asset_allowed: bool
    assets: list[AssetOut] = Field(default_factory=list)
    available: bool = Field(description="True only if some asset is available in this environment")

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"assets", "available"})


class WorkOut(BaseModel):
    id: UUID
    title: str
    authors: list[str]
    original_language: str | None
    authority_layer: ReferenceAuthorityLayer
    identifiers: list[Identifier]
    editions: list[EditionOut]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"editions", "created_at"})


class ExcerptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    edition_id: UUID
    asset_id: UUID | None
    location: str
    text: str
    language: str | None
    text_origin: TextOrigin
    verification_state: SourceVerificationState
    is_exact_quote: bool
    access_request_id: UUID | None
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"created_at"})


class AccessRequestIn(BaseModel):
    edition_id: UUID
    reason: str = Field(min_length=1, description="Why the source is needed")
    requested_scope: str = Field(min_length=1, description="Chapter, pages or section needed")
    surrounding_context: str | None = None
    acceptable_forms: list[AccessResponseForm] = Field(min_length=1)
    priority: Priority = Priority.MEDIUM


class TextResponseIn(BaseModel):
    form: Literal["EXACT_TEXT", "RESEARCHER_SUMMARY", "RESEARCHER_ATTESTATION"]
    location: str = Field(min_length=1)
    text: str = Field(min_length=1)
    language: str | None = None
    fulfills_request: bool = False


class AccessRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    edition_id: UUID
    reason: str
    requested_scope: str
    surrounding_context: str | None
    acceptable_forms: list[AccessResponseForm]
    priority: Priority
    status: SourceAccessRequestStatus
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"created_at"})


class AccessResponseOut(BaseModel):
    request: AccessRequestOut
    excerpt: ExcerptOut | None = None
    asset: AssetOut | None = None


class CancelIn(BaseModel):
    reason: str = Field(min_length=1)


class SourceLeadIn(BaseModel):
    statement: str = Field(min_length=1, description="e.g. 'I remember reading that author X said Y'")
    suspected_author: str | None = None
    suspected_work_id: UUID | None = None


class SourceLeadVerifyIn(BaseModel):
    excerpt_id: UUID


class SourceLeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    statement: str
    suspected_author: str | None
    suspected_work_id: UUID | None
    status: SourceLeadState
    verified_by_excerpt_id: UUID | None
    origin: SourceLeadOrigin = SourceLeadOrigin.RESEARCHER_MEMORY
    url: str | None = None
    title: str | None = None
    search_record_id: UUID | None = None
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"created_at"})


class SearchHit(BaseModel):
    chunk_id: UUID
    asset_id: UUID
    edition_id: UUID
    work_id: UUID
    work_title: str
    page_number: int
    char_start: int
    char_end: int
    snippet: str
    rank: float


class SearchResponse(BaseModel):
    """Retrieval finds candidates; it does not adjudicate truth (Core §39).

    `outcome` keeps "nothing found" distinct from execution failure (Core §72), and
    `scope` states what was actually searched so absence is bounded (Core §74.18).
    """

    query: str
    outcome: Literal["RESULTS_FOUND", "NO_RELEVANT_EVIDENCE_FOUND"]
    scope: str
    searched_assets: int
    hits: list[SearchHit]
    quotation_authority: Literal[False] = False


class PageExcerptIn(BaseModel):
    """Create an excerpt from an ingested page span. The server copies the text; clients never supply it."""

    page_number: int = Field(ge=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    is_exact_quote: bool = True
    expected_text: str | None = Field(
        default=None, description="If given, must equal the source span exactly or the request is rejected"
    )
