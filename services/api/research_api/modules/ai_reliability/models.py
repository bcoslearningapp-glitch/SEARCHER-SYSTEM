"""Recorded evaluation results per model and dimension (append-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, UUIDPrimaryKeyMixin, utcnow


class AIEvaluation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_evaluations"

    provider: Mapped[str] = mapped_column(String(40), index=True)
    model: Mapped[str] = mapped_column(String(200), index=True)
    dimension: Mapped[str] = mapped_column(String(60), index=True)
    score: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    comparator: Mapped[str] = mapped_column(String(2))
    passed: Mapped[bool] = mapped_column(Boolean)
    sample_size: Mapped[int] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(30))  # AUTOMATED_GOLDEN | HUMAN_GRADED
    fixture_set: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    recorded_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    run_id: Mapped[UUID | None] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
