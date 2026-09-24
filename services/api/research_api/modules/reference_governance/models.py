"""Foundational library, Qur'an text, Hadith records, reference reviews (PRD §18-21)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class FoundationalSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Logically isolated foundational library entry (FR-REFSRC-001)."""

    __tablename__ = "foundational_sources"
    __table_args__ = (
        CheckConstraint(
            "status <> 'APPROVED' OR (approved_by_kind = 'HUMAN' AND approved_at IS NOT NULL)", name="human_approval"
        ),
        Index(
            "uq_foundational_sources_one_approved_quran",
            "authority_layer",
            unique=True,
            postgresql_where=text("status = 'APPROVED' AND authority_layer = 'QURAN'"),
        ),
    )

    work_id: Mapped[UUID] = mapped_column(ForeignKey("source_works.id"), index=True)
    authority_layer: Mapped[str] = mapped_column(String(40))
    edition_version: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), index=True)
    sha256: Mapped[str] = mapped_column(String(64))
    dataset_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    staged_by_id: Mapped[str] = mapped_column(String(200))
    approved_by_kind: Mapped[str | None] = mapped_column(String(20))
    approved_by_id: Mapped[str | None] = mapped_column(String(200))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class QuranSurah(Base):
    __tablename__ = "quran_surahs"

    source_id: Mapped[UUID] = mapped_column(ForeignKey("foundational_sources.id"), primary_key=True)
    surah_number: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)


class QuranAyah(Base):
    """Exact ayah text as supplied by the approved dataset. Append-only (trigger)."""

    __tablename__ = "quran_ayat"

    source_id: Mapped[UUID] = mapped_column(ForeignKey("foundational_sources.id"), primary_key=True)
    surah_number: Mapped[int] = mapped_column(primary_key=True)
    ayah_number: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)


class HadithRecord(UUIDPrimaryKeyMixin, Base):
    """One narration per record; numbering is always tied to its edition scheme (FR-HADITH-001..003)."""

    __tablename__ = "hadith_records"
    __table_args__ = (
        UniqueConstraint("foundational_source_id", "numbering_scheme", "number", name="uq_hadith_records_number"),
    )

    foundational_source_id: Mapped[UUID] = mapped_column(ForeignKey("foundational_sources.id"), index=True)
    collection: Mapped[str] = mapped_column(Text)
    book: Mapped[str | None] = mapped_column(Text)
    chapter: Mapped[str | None] = mapped_column(Text)
    number: Mapped[str] = mapped_column(String(40))
    numbering_scheme: Mapped[str] = mapped_column(Text)
    narrator: Mapped[str | None] = mapped_column(Text)
    exact_text: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    entered_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReferenceReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reference_reviews"
    __table_args__ = (Index("ix_reference_reviews_target", "target_type", "target_id"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[UUID]
    question: Mapped[str] = mapped_column(Text)
    analytical_category: Mapped[str] = mapped_column(String(50))


class ReferenceEntry(UUIDPrimaryKeyMixin, Base):
    """One reasoning layer. Append-only; AI content is only ever SYSTEM_SYNTHESIS (DB check)."""

    __tablename__ = "reference_entries"
    __table_args__ = (
        CheckConstraint(
            "provenance->>'kind' <> 'AI_GENERATED' OR layer = 'SYSTEM_SYNTHESIS'", name="ai_only_synthesis"
        ),
        CheckConstraint(
            "layer <> 'SOURCE_TEXT' OR source_excerpt_id IS NOT NULL OR quran_ref IS NOT NULL"
            " OR hadith_record_id IS NOT NULL",
            name="source_text_is_sourced",
        ),
    )

    review_id: Mapped[UUID] = mapped_column(ForeignKey("reference_reviews.id"), index=True)
    layer: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(Text)
    source_excerpt_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_excerpts.id"))
    quran_ref: Mapped[str | None] = mapped_column(String(20))
    hadith_record_id: Mapped[UUID | None] = mapped_column(ForeignKey("hadith_records.id"))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReferenceJudgmentRecord(UUIDPrimaryKeyMixin, Base):
    """Judgments are append-only; the latest is current and earlier ones remain as history."""

    __tablename__ = "reference_judgments"
    __table_args__ = (
        CheckConstraint("judged_by_kind = 'HUMAN'", name="human_judge"),
        CheckConstraint("(state = 'RESERVED') = (reservation_type IS NOT NULL)", name="reservation_iff_reserved"),
    )

    review_id: Mapped[UUID] = mapped_column(ForeignKey("reference_reviews.id"), index=True)
    state: Mapped[str] = mapped_column(String(30))
    directness: Mapped[str] = mapped_column(String(20))
    reservation_type: Mapped[str | None] = mapped_column(String(30))
    divergence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    rationale: Mapped[str] = mapped_column(Text)
    judged_by_kind: Mapped[str] = mapped_column(String(20))
    judged_by_id: Mapped[str] = mapped_column(String(200))
    judged_by_role: Mapped[str | None] = mapped_column(String(40))
    decision_id: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
