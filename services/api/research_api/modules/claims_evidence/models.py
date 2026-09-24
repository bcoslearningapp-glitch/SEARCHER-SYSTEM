"""Claims, assumptions and open questions (Core §14-19, §37)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Claim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "claims"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(30))
    statement_origin: Mapped[str] = mapped_column(String(30))
    workflow_state: Mapped[str] = mapped_column(String(20))
    epistemic_strength: Mapped[str] = mapped_column(String(30))
    important: Mapped[bool] = mapped_column(default=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_note_id: Mapped[UUID | None] = mapped_column(ForeignKey("scratch_notes.id"))


class Assumption(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assumptions"
    __table_args__ = (
        # AI-inferred assumptions stay labeled as such until a human confirms or reclassifies them.
        CheckConstraint("origin <> 'SYSTEM_INFERRED' OR provenance->>'kind' = 'AI_GENERATED'", name="inferred_is_ai"),
    )

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(20))
    criticality: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    claim_id: Mapped[UUID | None] = mapped_column(ForeignKey("claims.id"))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    review_note: Mapped[str | None] = mapped_column(Text)
    source_note_id: Mapped[UUID | None] = mapped_column(ForeignKey("scratch_notes.id"))


class OpenQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "open_questions"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    conclusion: Mapped[str | None] = mapped_column(String(40))
    source_note_id: Mapped[UUID | None] = mapped_column(ForeignKey("scratch_notes.id"))


class Evidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Source-derived finding related to a target; never the source itself (Core §32)."""

    __tablename__ = "evidence"
    __table_args__ = (
        Index("ix_evidence_target", "target_type", "target_id"),
        CheckConstraint("status <> 'ACCEPTED' OR assessment IS NOT NULL", name="accepted_has_assessment"),
    )

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[UUID]
    role: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), index=True)
    finding: Mapped[str] = mapped_column(Text)
    # Evidence must terminate at a source excerpt; AI text cannot stand in for it (Core §36).
    excerpt_id: Mapped[UUID] = mapped_column(ForeignKey("source_excerpts.id"))
    track: Mapped[str | None] = mapped_column(String(30))
    assessment: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    assessed_by_id: Mapped[str | None] = mapped_column(String(200))


class SourceLineage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Dependency between source works (Core §35)."""

    __tablename__ = "source_lineage"
    __table_args__ = (
        UniqueConstraint("from_work_id", "relation", "to_work_id", name="uq_source_lineage_edge"),
        CheckConstraint("from_work_id <> to_work_id", name="no_self_lineage"),
    )

    from_work_id: Mapped[UUID] = mapped_column(ForeignKey("source_works.id"), index=True)
    relation: Mapped[str] = mapped_column(String(20))
    to_work_id: Mapped[UUID] = mapped_column(ForeignKey("source_works.id"), index=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[str] = mapped_column(String(200))


class ResearchTrackRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A recorded support/challenge/alternative search and its bounded outcome (Core §41, §72)."""

    __tablename__ = "research_track_runs"
    __table_args__ = (Index("ix_research_track_runs_target", "target_type", "target_id"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[UUID]
    track: Mapped[str] = mapped_column(String(30))
    outcome: Mapped[str] = mapped_column(String(40))
    scope: Mapped[str] = mapped_column(Text)
    queries: Mapped[list[str]] = mapped_column(JSONB, default=list)
    performed_by_id: Mapped[str] = mapped_column(String(200))
