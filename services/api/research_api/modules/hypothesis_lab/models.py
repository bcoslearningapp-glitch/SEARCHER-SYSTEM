"""Hypotheses (with immutable versions) and mechanisms (Core §20-22)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class Hypothesis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Current pointer; history lives in immutable `hypothesis_versions` (FR-HYP-004)."""

    __tablename__ = "hypotheses"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    current_version: Mapped[int]
    lifecycle_state: Mapped[str] = mapped_column(String(30))
    epistemic_state: Mapped[str] = mapped_column(String(20))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class HypothesisVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "hypothesis_versions"
    __table_args__ = (UniqueConstraint("hypothesis_id", "version_number", name="uq_hypothesis_versions_number"),)

    hypothesis_id: Mapped[UUID] = mapped_column(ForeignKey("hypotheses.id"), index=True)
    version_number: Mapped[int]
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    lifecycle_state: Mapped[str] = mapped_column(String(30))
    epistemic_state: Mapped[str] = mapped_column(String(20))
    change_reason: Mapped[str] = mapped_column(Text)
    actor_kind: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str] = mapped_column(String(200))
    actor_role: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Mechanism(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mechanisms"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class HypothesisMechanism(Base):
    __tablename__ = "hypothesis_mechanisms"

    hypothesis_id: Mapped[UUID] = mapped_column(ForeignKey("hypotheses.id"), primary_key=True)
    mechanism_id: Mapped[UUID] = mapped_column(ForeignKey("mechanisms.id"), primary_key=True)


class HypothesisCompetition(Base):
    """Competing hypotheses (FR-HYP-005); stored once per pair with a < b."""

    __tablename__ = "hypothesis_competitions"

    hypothesis_a_id: Mapped[UUID] = mapped_column(ForeignKey("hypotheses.id"), primary_key=True)
    hypothesis_b_id: Mapped[UUID] = mapped_column(ForeignKey("hypotheses.id"), primary_key=True)
    note: Mapped[str | None] = mapped_column(Text)
