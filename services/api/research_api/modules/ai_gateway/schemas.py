"""AI gateway API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileOut(BaseModel):
    name: str
    provider: str
    model: str
    effort: str
    local: bool
    configured: bool
    default: bool


class AIPolicyOut(BaseModel):
    project_id: UUID
    cloud_consent: bool
    allowed_profiles: list[str]
    preferred_profile: str | None
    project_budget_usd: Decimal | None
    task_budget_usd: Decimal | None
    spent_usd: Decimal


class AIPolicyUpdate(BaseModel):
    cloud_consent: bool
    allowed_profiles: list[str] = Field(default_factory=list, description="Empty means any configured profile")
    preferred_profile: str | None = None
    project_budget_usd: Decimal | None = Field(default=None, ge=0)
    task_budget_usd: Decimal | None = Field(default=None, ge=0)
    reason: str | None = None


class AIRequestOut(BaseModel):
    id: UUID
    task: str
    template_version: str
    profile: str
    provider: str
    model: str
    status: str
    error_kind: str | None
    disclosure_reason: str
    sensitivity: str
    entity_ids: list[str]
    outbound_chars: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal
    served_by_fallback: bool
    created_at: datetime
