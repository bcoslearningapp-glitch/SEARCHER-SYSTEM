"""Local knowledge items with versioned lifecycle, and explicit cross-project reuse (PRD §28-29, §35)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class KnowledgeItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Current state; every change appends a KnowledgeVersion with the full content."""

    __tablename__ = "knowledge_items"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    current_version: Mapped[int] = mapped_column(Integer)
    statement: Mapped[str] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    scope: Mapped[str] = mapped_column(Text)
    contexts: Mapped[list[str]] = mapped_column(JSONB)
    evidence_basis: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    contrary_evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    contrary_evidence_searched: Mapped[bool] = mapped_column(Boolean)
    confidence: Mapped[str] = mapped_column(String(30))
    temporal_profile: Mapped[str] = mapped_column(String(20))
    valid_from: Mapped[date | None] = mapped_column(Date)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revalidation_interval_days: Mapped[int | None] = mapped_column(Integer)
    source_version: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class KnowledgeVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_versions"
    __table_args__ = (UniqueConstraint("knowledge_item_id", "version_number"),)

    knowledge_item_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    change: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    gate_evaluation_id: Mapped[UUID | None]
    actor: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KnowledgeReuse(UUIDPrimaryKeyMixin, Base):
    """A human-assessed, labelled reuse in another project; nothing is copied as evidence."""

    __tablename__ = "knowledge_reuses"

    knowledge_item_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    knowledge_version: Mapped[int] = mapped_column(Integer)
    target_project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    transferability: Mapped[str] = mapped_column(String(30))
    rationale: Mapped[str] = mapped_column(Text)
    differences: Mapped[str | None] = mapped_column(Text)
    assessed_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
