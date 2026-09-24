"""Research planning persistence. Plans are versioned; search records and sufficiency assessments are append-only."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, UUIDPrimaryKeyMixin, utcnow


class ResearchPlan(UUIDPrimaryKeyMixin, Base):
    """One version of the plan for a research question (FR-RSCH-001/002). Content never changes after creation."""

    __tablename__ = "research_plans"
    __table_args__ = (UniqueConstraint("project_id", "series_id", "version_number"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    series_id: Mapped[UUID] = mapped_column(index=True)  # all versions of one question share it
    version_number: Mapped[int] = mapped_column(Integer)
    supersedes_id: Mapped[UUID | None] = mapped_column(ForeignKey("research_plans.id"))
    status: Mapped[str] = mapped_column(String(20))  # ACTIVE | SUPERSEDED
    question: Mapped[str] = mapped_column(Text)
    decision_served: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(30))
    risk_impact: Mapped[str] = mapped_column(Text, default="")
    desired_evidence_types: Mapped[list[str]] = mapped_column(JSONB, default=list)
    languages: Mapped[list[str]] = mapped_column(JSONB, default=list)
    tracks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    sufficiency_criteria: Mapped[list[str]] = mapped_column(JSONB)
    max_web_searches: Mapped[int | None] = mapped_column(Integer)
    change_reason: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SearchRecord(UUIDPrimaryKeyMixin, Base):
    """Search audit (FR-WEB-005). Append-only; outcome keeps failure distinct from absence (FR-WEB-004)."""

    __tablename__ = "search_records"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("research_plans.id"), index=True)
    track: Mapped[str | None] = mapped_column(String(30))
    question: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(40))
    queries: Mapped[list[str]] = mapped_column(JSONB)
    languages: Mapped[list[str]] = mapped_column(JSONB, default=list)
    outcome: Mapped[str] = mapped_column(String(40))
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    scope: Mapped[str] = mapped_column(Text)
    exclusions: Mapped[str | None] = mapped_column(Text)
    ai_request_id: Mapped[UUID | None]
    actor: Mapped[dict[str, Any]] = mapped_column(JSONB)
    provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SufficiencyAssessment(UUIDPrimaryKeyMixin, Base):
    """Human, decision-relative sufficiency conclusion (FR-SUFF-001..003). Append-only; the latest is current."""

    __tablename__ = "sufficiency_assessments"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("research_plans.id"), index=True)
    decision_served: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(String(40))
    considerations: Mapped[dict[str, str]] = mapped_column(JSONB)
    rationale: Mapped[str] = mapped_column(Text)
    recommend_experiment: Mapped[bool] = mapped_column(Boolean, default=False)
    signals: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    assessed_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
