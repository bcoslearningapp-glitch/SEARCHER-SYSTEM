"""Source identity persistence: SourceWork ≠ SourceEdition ≠ SourceAsset (Core §23, FR-SRC-001..003)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class SourceWork(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The intellectual work. Library-wide, not owned by a project."""

    __tablename__ = "source_works"

    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[list[str]] = mapped_column(JSONB, default=list)
    original_language: Mapped[str | None] = mapped_column(String(20))
    authority_layer: Mapped[str] = mapped_column(String(40), index=True)
    identifiers: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    created_by_id: Mapped[str] = mapped_column(String(200))


class SourceEdition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_editions"

    work_id: Mapped[UUID] = mapped_column(ForeignKey("source_works.id"), index=True)
    edition_label: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(20))
    translator: Mapped[str | None] = mapped_column(Text)
    publisher: Mapped[str | None] = mapped_column(Text)
    published_date: Mapped[str | None] = mapped_column(String(40))
    identifiers: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    verification_state: Mapped[str] = mapped_column(String(40))
    license_note: Mapped[str | None] = mapped_column(Text)
    portable_asset_allowed: Mapped[bool] = mapped_column(default=False)


class SourceAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A concrete file/object/holding. Availability is environment-specific (FR-SRC-003)."""

    __tablename__ = "source_assets"

    edition_id: Mapped[UUID] = mapped_column(ForeignKey("source_editions.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    access_mode: Mapped[str] = mapped_column(String(30))
    available_in_environment: Mapped[bool]
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    media_type: Mapped[str | None] = mapped_column(String(100))
    byte_size: Mapped[int | None] = mapped_column(BigInteger)
    storage_key: Mapped[str | None] = mapped_column(String(100))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    text_origin: Mapped[str | None] = mapped_column(String(30))
    holding_note: Mapped[str | None] = mapped_column(Text)
    ingestion_status: Mapped[str] = mapped_column(String(20), default="NOT_APPLICABLE")
    ingestion_job_id: Mapped[UUID | None]
    access_request_id: Mapped[UUID | None]


class ProjectSource(Base):
    """A work in use by a project."""

    __tablename__ = "project_sources"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    work_id: Mapped[UUID] = mapped_column(ForeignKey("source_works.id"), primary_key=True)
    added_by_id: Mapped[str] = mapped_column(String(200))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SourceExcerpt(UUIDPrimaryKeyMixin, Base):
    """Located source content. Text and trust fields are immutable (trigger, migration 0003)."""

    __tablename__ = "source_excerpts"
    __table_args__ = (
        # OCR text is never an exact quote until verified (Core §28, FR-INGEST-003).
        CheckConstraint(
            "NOT (text_origin = 'OCR_EXTRACTED' AND is_exact_quote"
            " AND verification_state NOT IN ('MACHINE_VERIFIED', 'RESEARCHER_SUPPLIED_EXACT'))",
            name="ocr_not_exact_unless_verified",
        ),
    )

    edition_id: Mapped[UUID] = mapped_column(ForeignKey("source_editions.id"), index=True)
    asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_assets.id"))
    location: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(20))
    text_origin: Mapped[str] = mapped_column(String(30))
    verification_state: Mapped[str] = mapped_column(String(40))
    is_exact_quote: Mapped[bool]
    access_request_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_access_requests.id"))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SourceAccessRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Targeted request for a known-but-unavailable source (FR-HYBRID-001/002)."""

    __tablename__ = "source_access_requests"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    edition_id: Mapped[UUID] = mapped_column(ForeignKey("source_editions.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    requested_scope: Mapped[str] = mapped_column(Text)
    surrounding_context: Mapped[str | None] = mapped_column(Text)
    acceptable_forms: Mapped[list[str]] = mapped_column(JSONB)
    priority: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), index=True)
    created_by_kind: Mapped[str] = mapped_column(String(20))
    created_by_id: Mapped[str] = mapped_column(String(200))


class SourceLead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Researcher memory of a source: a lead, never evidence, until verified (Core §27)."""

    __tablename__ = "source_leads"
    __table_args__ = (
        CheckConstraint("status <> 'VERIFIED' OR verified_by_excerpt_id IS NOT NULL", name="verified_has_excerpt"),
    )

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    suspected_author: Mapped[str | None] = mapped_column(Text)
    suspected_work_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_works.id"))
    status: Mapped[str] = mapped_column(String(20))
    verified_by_excerpt_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_excerpts.id"))
    created_by_id: Mapped[str] = mapped_column(String(200))
    # Web results enter as leads, never evidence (FR-WEB-003). URL and title are untrusted text.
    origin: Mapped[str] = mapped_column(String(30), default="RESEARCHER_MEMORY", server_default="RESEARCHER_MEMORY")
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    search_record_id: Mapped[UUID | None] = mapped_column(index=True)
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class SourcePage(UUIDPrimaryKeyMixin, Base):
    """Extracted page text with its anchor. Derived data; the original asset stays authoritative."""

    __tablename__ = "source_pages"
    __table_args__ = (UniqueConstraint("asset_id", "page_number", name="uq_source_pages_asset_page"),)

    asset_id: Mapped[UUID] = mapped_column(ForeignKey("source_assets.id"), index=True)
    page_number: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    text_origin: Mapped[str] = mapped_column(String(30))
    needs_ocr: Mapped[bool] = mapped_column(default=False)


class SourceChunk(UUIDPrimaryKeyMixin, Base):
    """Discovery unit for retrieval, never a quotation authority (FR-INGEST-004)."""

    __tablename__ = "source_chunks"
    __table_args__ = (Index("ix_source_chunks_tsv", "tsv", postgresql_using="gin"),)

    asset_id: Mapped[UUID] = mapped_column(ForeignKey("source_assets.id"), index=True)
    page_number: Mapped[int]
    chunk_index: Mapped[int]
    char_start: Mapped[int]
    char_end: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    tsv: Mapped[Any] = mapped_column(TSVECTOR, Computed("to_tsvector('simple', text)", persisted=True))


class SourceChunkEmbedding(Base):
    """A chunk's vector for one embedding model (ADR-025). Derived data: rebuilt, never exported."""

    __tablename__ = "source_chunk_embeddings"

    chunk_id: Mapped[UUID] = mapped_column(ForeignKey("source_chunks.id", ondelete="CASCADE"), primary_key=True)
    model: Mapped[str] = mapped_column(String(200), primary_key=True, index=True)
    dimensions: Mapped[int]
    embedding: Mapped[Any] = mapped_column(Vector())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
