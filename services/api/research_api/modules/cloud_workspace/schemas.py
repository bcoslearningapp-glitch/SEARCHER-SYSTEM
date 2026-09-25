"""Cloud workspace API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Only text records a person can read are staged. File assets never leave the installation (ADR-023).
StageableKind = Literal["SourceExcerpt", "Claim", "Hypothesis", "OutputVersion"]
KINDS: tuple[str, ...] = ("SourceExcerpt", "Claim", "Hypothesis", "OutputVersion")


class StageItem(BaseModel):
    entity_type: StageableKind
    entity_id: UUID


class StageIn(BaseModel):
    purpose: str = Field(min_length=3, max_length=2000)
    items: list[StageItem] = Field(min_length=1, max_length=200)
    ttl_hours: int | None = Field(default=None, ge=1, description="Defaults to the configured TTL")


class DeleteIn(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class StagedItemOut(BaseModel):
    entity_type: str
    entity_id: UUID
    sha256: str
    byte_size: int
    remote_ref: str | None


class StagingOut(BaseModel):
    id: UUID
    project_id: UUID
    adapter: str
    purpose: str
    status: Literal["ACTIVE", "BLOCKED", "DELETED", "EXPIRED"]
    sensitivity: str
    policy_decision: dict[str, Any]
    expires_at: datetime | None
    staged_by: dict[str, Any]
    created_at: datetime
    deleted_at: datetime | None
    deleted_by: dict[str, Any] | None
    delete_reason: str | None
    items: list[StagedItemOut]


class WorkspaceInfoOut(BaseModel):
    adapter: str
    enabled: bool
    remote: bool
    default_ttl_hours: int
    max_ttl_hours: int
    kinds: list[str]


class PurgeOut(BaseModel):
    expired: list[UUID]
