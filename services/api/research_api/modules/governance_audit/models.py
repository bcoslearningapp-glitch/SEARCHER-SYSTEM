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


class ApprovalRecord(UUIDPrimaryKeyMixin, Base):
    """Explicit human approval (FR-APPROVAL-001). Append-only; human actors only."""

    __tablename__ = "approvals"
    __table_args__ = (
        CheckConstraint("approver_kind = 'HUMAN'", name="human_approver"),
        Index("ix_approvals_subject", "subject_type", "subject_id"),
    )

    project_id: Mapped[UUID] = mapped_column(index=True)
    subject_type: Mapped[str] = mapped_column(String(100))
    subject_id: Mapped[UUID]
    outcome: Mapped[str] = mapped_column(String(20))
    approver_kind: Mapped[str] = mapped_column(String(20))
    approver_id: Mapped[str] = mapped_column(String(200))
    approver_role: Mapped[str | None] = mapped_column(String(40))
    reason: Mapped[str | None] = mapped_column(Text)
    methodology_path: Mapped[str] = mapped_column(String(40))
    gate_evaluation_id: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QualityGateEvaluationRecord(UUIDPrimaryKeyMixin, Base):
    """Stored gate results so 'Why?' explanations use recorded data (PRD §66). Append-only."""

    __tablename__ = "quality_gate_evaluations"
    __table_args__ = (Index("ix_quality_gate_evaluations_subject", "subject_type", "subject_id"),)

    project_id: Mapped[UUID | None] = mapped_column(index=True)
    gate: Mapped[str] = mapped_column(String(40))
    subject_type: Mapped[str | None] = mapped_column(String(100))
    subject_id: Mapped[UUID | None]
    result: Mapped[str] = mapped_column(String(30))
    risk_level: Mapped[str] = mapped_column(String(20))
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    methodology_version: Mapped[str] = mapped_column(String(20))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DecisionRecord(UUIDPrimaryKeyMixin, Base):
    """Decision with AI recommendation kept separate from the human decision (FR-DEC-001/002)."""

    __tablename__ = "decisions"
    __table_args__ = (
        CheckConstraint(
            "status <> 'DECIDED' OR (decided_by_kind = 'HUMAN' AND final_decision IS NOT NULL"
            " AND human_justification IS NOT NULL)",
            name="human_decides",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(index=True)
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSONB, default=list)
    ai_recommendation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    rationale: Mapped[str | None] = mapped_column(Text)
    required_role: Mapped[str] = mapped_column(String(40))
    blocking: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True)
    subject_type: Mapped[str | None] = mapped_column(String(100))
    subject_id: Mapped[UUID | None]
    final_decision: Mapped[str | None] = mapped_column(Text)
    human_justification: Mapped[str | None] = mapped_column(Text)
    methodology_path: Mapped[str | None] = mapped_column(String(40))
    decided_by_kind: Mapped[str | None] = mapped_column(String(20))
    decided_by_id: Mapped[str | None] = mapped_column(String(200))
    decided_by_role: Mapped[str | None] = mapped_column(String(40))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_kind: Mapped[str] = mapped_column(String(20))
    created_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
