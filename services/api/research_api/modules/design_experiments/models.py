"""Design requirement versions and design concepts. Requirement text is never edited (a revision supersedes)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class DesignRequirement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "design_requirements"
    __table_args__ = (UniqueConstraint("series_id", "version_number"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    series_id: Mapped[UUID] = mapped_column(index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    supersedes_id: Mapped[UUID | None] = mapped_column(ForeignKey("design_requirements.id"))
    statement: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10))
    traces: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), index=True)
    change_reason: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DesignConcept(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "design_concepts"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(30))
    origin_reference: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), index=True)
    hypothesis_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    mechanism_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    derived_from_concept_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    rejection: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    selection: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ConceptCoverage(Base):
    """How a concept addresses a requirement series (the current version is what counts)."""

    __tablename__ = "design_concept_coverage"

    concept_id: Mapped[UUID] = mapped_column(ForeignKey("design_concepts.id"), primary_key=True)
    requirement_series_id: Mapped[UUID] = mapped_column(primary_key=True)
    requirement_id: Mapped[UUID] = mapped_column(ForeignKey("design_requirements.id"))  # version judged
    coverage: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
