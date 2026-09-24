"""Project aggregate persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(500))
    initial_input: Mapped[str] = mapped_column(Text)
    input_type: Mapped[str] = mapped_column(String(40))
    sensitivity: Mapped[str] = mapped_column(String(20))
    risk_level: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), index=True)
    research_mode: Mapped[str] = mapped_column(String(30))
    primary_language: Mapped[str] = mapped_column(String(5))
    forked_from_project_id: Mapped[UUID | None] = mapped_column(ForeignKey("projects.id"))

    core_schema_version: Mapped[str] = mapped_column(String(20))
    methodology_version: Mapped[str] = mapped_column(String(20))
    constitution_version: Mapped[str] = mapped_column(String(20))

    owner_kind: Mapped[str] = mapped_column(String(20))
    owner_id: Mapped[str] = mapped_column(String(200))
    owner_role: Mapped[str | None] = mapped_column(String(40))


class ResearchState(Base):
    """Durable Research State, one row per project (FR-STATE-001/002)."""

    __tablename__ = "research_states"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    current_question: Mapped[str | None] = mapped_column(Text)
    established_findings: Mapped[list[str]] = mapped_column(JSONB, default=list)
    unresolved_items: Mapped[list[str]] = mapped_column(JSONB, default=list)
    active_hypothesis_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    reservations: Mapped[list[str]] = mapped_column(JSONB, default=list)
    blockers: Mapped[list[str]] = mapped_column(JSONB, default=list)
    next_action: Mapped[str | None] = mapped_column(Text)
    next_action_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ProjectClosure(UUIDPrimaryKeyMixin, Base):
    """Closure records are append-only and survive reopening (FR-CLOSE-002, FR-REOPEN-001)."""

    __tablename__ = "project_closures"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    closure_type: Mapped[str] = mapped_column(String(40))
    record: Mapped[dict[str, Any]] = mapped_column(JSONB)
    closed_by_id: Mapped[str] = mapped_column(String(200))
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reopen_trigger: Mapped[str | None] = mapped_column(Text)
    gate_evaluation_id: Mapped[UUID | None]
    approval_id: Mapped[UUID | None]


class ScratchNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Free-thinking space: never automatically promoted to formal knowledge (Core §65)."""

    __tablename__ = "scratch_notes"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    author_id: Mapped[str] = mapped_column(String(200))
    captured_as: Mapped[str | None] = mapped_column(String(60))
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProblemFrameVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Versioned Problem Frame. Approved/superseded rows are immutable (DB trigger, migration 0002)."""

    __tablename__ = "problem_frame_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "version_number", name="uq_problem_frame_versions_project_version"),
        Index(
            "uq_problem_frame_versions_one_draft",
            "project_id",
            unique=True,
            postgresql_where=text("status = 'DRAFT'"),
        ),
        Index(
            "uq_problem_frame_versions_one_approved",
            "project_id",
            unique=True,
            postgresql_where=text("status = 'APPROVED'"),
        ),
    )

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    version_number: Mapped[int]
    status: Mapped[str] = mapped_column(String(20))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    supersedes_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("problem_frame_versions.id"))
    approval_id: Mapped[UUID | None]
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
