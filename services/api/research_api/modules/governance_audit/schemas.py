"""Validated inputs/outputs for the audit framework, aligned with event.schema.json."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from research_api.contracts.enums import ActorKind, ActorRole

_ACTION = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
_EVENT_TYPE = re.compile(r"^[A-Z][A-Za-z]+$")


class Actor(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ActorKind
    id: str = Field(min_length=1, max_length=200)
    role: ActorRole | None = None


class AIActionRecord(BaseModel):
    """Reproducibility metadata for a material AI action (Core §71, PRD §53)."""

    model_config = ConfigDict(frozen=True)

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    supplied_entity_ids: list[UUID] = Field(default_factory=list)
    task_id: str | None = None
    timestamp: datetime


class _EventInput(BaseModel):
    project_id: UUID | None = None
    entity_type: str | None = Field(default=None, max_length=100)
    entity_id: UUID | None = None
    actor: Actor


class AuditEntry(_EventInput):
    action: str = Field(description="dotted verb, e.g. problem_frame.approve")
    previous_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None
    reason: str | None = None
    ai_action: AIActionRecord | None = None

    @field_validator("action")
    @classmethod
    def _action_format(cls, value: str) -> str:
        if not _ACTION.match(value):
            raise ValueError("action must be a dotted lower_snake verb such as 'problem_frame.approve'")
        return value

    @model_validator(mode="after")
    def _ai_actions_carry_provenance(self) -> Self:
        if self.actor.kind is ActorKind.AI and self.ai_action is None:
            raise ValueError("AI-actor audit entries must include ai_action provenance (Core §71)")
        return self


class ResearchEventEntry(_EventInput):
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def _event_type_format(cls, value: str) -> str:
        if not _EVENT_TYPE.match(value):
            raise ValueError("event_type must be PascalCase, e.g. 'ProblemFrameApproved'")
        return value


class VersionContext(BaseModel):
    core_schema_version: str
    methodology_version: str
    constitution_version: str


class AuditEventOut(BaseModel):
    id: UUID
    project_id: UUID | None
    action: str
    entity_type: str | None
    entity_id: UUID | None
    occurred_at: datetime
    actor: Actor
    versions: VersionContext
    previous_state: dict[str, Any] | None
    new_state: dict[str, Any] | None
    reason: str | None
    ai_action: AIActionRecord | None

    def to_contract(self) -> dict[str, Any]:
        """Serialize to the canonical contract shape (event.schema.json#AuditEvent)."""
        return self.model_dump(mode="json", exclude_none=True)
