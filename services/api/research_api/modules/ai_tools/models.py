"""Append-only audit of every AI tool call, including refused ones (FR-AI-TOOL-004/005, PRD §53)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, UUIDPrimaryKeyMixin, utcnow


class AIToolCall(UUIDPrimaryKeyMixin, Base):
    """Written in its own transaction so refused and failed calls stay visible when the task rolls back.

    `project_id` is indexed but not a foreign key for the same reason. Outputs are
    recorded as entity ids plus a digest, never as full source text.
    """

    __tablename__ = "ai_tool_calls"

    project_id: Mapped[UUID] = mapped_column(index=True)
    job_id: Mapped[UUID | None] = mapped_column(index=True)
    ai_request_id: Mapped[UUID | None]
    tool: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))  # OK | DENIED | INVALID | ERROR
    reason: Mapped[str | None] = mapped_column(Text)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSONB)
    output_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    output_sha256: Mapped[str | None] = mapped_column(String(64))
    principal_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
