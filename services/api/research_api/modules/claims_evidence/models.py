"""Claims, assumptions and open questions (Core §14-19, §37)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
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
