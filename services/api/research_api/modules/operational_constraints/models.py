"""Operational reality: law, regulation, contracts, licenses, institutional rules (Core §5, PRD §5.3)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OperationalConstraint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Kept in its own table so it can never overwrite or stand in for a reference judgment."""

    __tablename__ = "operational_constraints"
    __table_args__ = (Index("ix_operational_constraints_target", "target_type", "target_id"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[UUID]
    kind: Mapped[str] = mapped_column(String(30))
    state: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(Text)
    source_reference: Mapped[str | None] = mapped_column(Text)
    required_change: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution: Mapped[str | None] = mapped_column(Text)
