"""AI gateway persistence: per-project AI policy and the outbound request log (PRD §54, §64)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, UUIDPrimaryKeyMixin, utcnow


class ProjectAIPolicy(Base):
    """Human-set AI configuration for one project. Absent row = defaults (no consent, no budget)."""

    __tablename__ = "project_ai_policies"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    cloud_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_profiles: Mapped[list[str]] = mapped_column(JSONB, default=list)
    preferred_profile: Mapped[str | None] = mapped_column(String(100))
    project_budget_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    task_budget_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    updated_by_id: Mapped[str] = mapped_column(String(200))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AIRequestRecord(UUIDPrimaryKeyMixin, Base):
    """Append-only disclosure and usage record for every attempted AI request (FR-DATA-001, FR-COST-001).

    Written in its own transaction so blocked and failed requests stay traceable
    even when the calling operation rolls back. `project_id` is deliberately not a
    foreign key for the same reason.
    """

    __tablename__ = "ai_requests"

    project_id: Mapped[UUID | None] = mapped_column(index=True)
    task: Mapped[str] = mapped_column(String(100))
    template_version: Mapped[str] = mapped_column(String(40))
    profile: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    error_kind: Mapped[str | None] = mapped_column(String(60))
    disclosure_reason: Mapped[str] = mapped_column(Text)
    sensitivity: Mapped[str] = mapped_column(String(20))
    entity_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    outbound_chars: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal(0))
    served_by_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    provider_request_id: Mapped[str | None] = mapped_column(String(200))
    principal_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
