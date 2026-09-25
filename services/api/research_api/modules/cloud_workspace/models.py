"""Disclosure manifest for the selective cloud workspace (FR-CLOUD-003, ADR-023)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, UUIDPrimaryKeyMixin, utcnow


class WorkspaceStaging(UUIDPrimaryKeyMixin, Base):
    """One explicit staging request. Kept for ever; only its status moves forward (ACTIVE -> DELETED/EXPIRED)."""

    __tablename__ = "workspace_stagings"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    adapter: Mapped[str] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), index=True)
    sensitivity: Mapped[str] = mapped_column(String(20))
    policy_decision: Mapped[dict[str, Any]] = mapped_column(JSONB)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    staged_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    delete_reason: Mapped[str | None] = mapped_column(Text)


class WorkspaceStagedItem(UUIDPrimaryKeyMixin, Base):
    """What was (or, when blocked, would have been) disclosed. Append-only."""

    __tablename__ = "workspace_staged_items"

    staging_id: Mapped[UUID] = mapped_column(ForeignKey("workspace_stagings.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[UUID] = mapped_column(Uuid)
    sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    remote_ref: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
