"""Controlled AI tools HTTP API: definitions and the per-project call log."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from research_api.modules.ai_tools import registry
from research_api.modules.ai_tools import tools as _tools  # noqa: F401 - registers the tools
from research_api.modules.ai_tools.models import AIToolCall
from research_api.modules.project_workflow import service as projects
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1", tags=["ai tools"])


class ToolCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID | None
    ai_request_id: UUID | None
    tool: str
    kind: str
    status: str
    reason: str | None
    arguments: dict[str, Any]
    output_ids: list[str]
    output_sha256: str | None
    principal_id: str
    created_at: datetime


@router.get("/ai/tools")
def list_tools() -> list[dict[str, Any]]:
    """Provider-neutral definitions of every registered tool (FR-AI-TOOL-003)."""
    return registry.definitions()


@router.get("/projects/{project_id}/ai-tool-calls", response_model=list[ToolCallOut])
def list_calls(project_id: UUID, db: DBSession, limit: int = 200) -> list[ToolCallOut]:
    projects.get_project(db, project_id)
    rows = db.scalars(
        select(AIToolCall)
        .where(AIToolCall.project_id == project_id)
        .order_by(AIToolCall.created_at.desc())
        .limit(min(max(limit, 1), 500))
    )
    return [ToolCallOut.model_validate(r) for r in rows]
