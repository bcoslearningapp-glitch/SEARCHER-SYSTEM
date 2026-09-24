"""Outputs and their immutable versions (PRD §37)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class Output(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outputs"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    output_type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(5))
    mode: Mapped[str] = mapped_column(String(20))
    subject_type: Mapped[str | None] = mapped_column(String(60))
    subject_id: Mapped[UUID | None]
    current_version: Mapped[int] = mapped_column(Integer)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class OutputVersion(UUIDPrimaryKeyMixin, Base):
    """Content is immutable; only the status moves forward (DB trigger)."""

    __tablename__ = "output_versions"
    __table_args__ = (UniqueConstraint("output_id", "version_number"),)

    output_id: Mapped[UUID] = mapped_column(ForeignKey("outputs.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    change_reason: Mapped[str | None] = mapped_column(Text)
    approval_id: Mapped[UUID | None]
    created_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
