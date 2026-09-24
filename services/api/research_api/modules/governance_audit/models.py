"""Persistence for audit and research events.

Both tables are append-only: a database trigger (migration 0001) rejects
UPDATE and DELETE so history cannot be silently rewritten (PRD §60.3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, UUIDPrimaryKeyMixin, utcnow


class _EventColumns(UUIDPrimaryKeyMixin):
    project_id: Mapped[UUID | None] = mapped_column(index=True)
    entity_type: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped[UUID | None]
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    actor_kind: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str] = mapped_column(String(200))
    actor_role: Mapped[str | None] = mapped_column(String(40))

    core_schema_version: Mapped[str] = mapped_column(String(20))
    methodology_version: Mapped[str] = mapped_column(String(20))
    constitution_version: Mapped[str] = mapped_column(String(20))


class AuditEventRecord(_EventColumns, Base):
    """Who did what to which entity, with previous/new state (PRD §67)."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_entity", "entity_type", "entity_id"),
        # Mirrors the contract rule: AI actions always carry provenance (Core §71).
        CheckConstraint("actor_kind <> 'AI' OR ai_action IS NOT NULL", name="ai_provenance"),
    )

    action: Mapped[str] = mapped_column(String(120))
    previous_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(Text)
    ai_action: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class ResearchEventRecord(_EventColumns, Base):
    """Meaningful research change such as ProblemFrameApproved (Core §56)."""

    __tablename__ = "research_events"
    __table_args__ = (Index("ix_research_events_entity", "entity_type", "entity_id"),)

    event_type: Mapped[str] = mapped_column(String(120))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
