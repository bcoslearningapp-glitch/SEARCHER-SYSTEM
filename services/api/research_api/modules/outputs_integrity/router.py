"""Output HTTP API (PRD §37)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.outputs_integrity import service
from research_api.modules.outputs_integrity.schemas import (
    ApproveIn,
    ApproveOut,
    OutputIn,
    OutputOut,
    ReviseIn,
    SettingsIn,
    VersionOut,
)
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}/outputs", tags=["outputs"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("", response_model=list[OutputOut])
def list_outputs(project_id: UUID, db: DB) -> list[OutputOut]:
    return service.list_outputs(db, project_id)


@router.post("", response_model=OutputOut, status_code=status.HTTP_201_CREATED)
def create_output(project_id: UUID, data: OutputIn, db: DB, who: Who) -> OutputOut:
    return service.create_output(db, who, project_id, data)


@router.get("/{output_id}", response_model=OutputOut)
def get_output(project_id: UUID, output_id: UUID, db: DB) -> OutputOut:
    return service.get_output(db, project_id, output_id)


@router.get("/{output_id}/versions", response_model=list[VersionOut])
def list_versions(project_id: UUID, output_id: UUID, db: DB) -> list[VersionOut]:
    return service.list_versions(db, project_id, output_id)


@router.post("/{output_id}/recompose", response_model=OutputOut)
def recompose(project_id: UUID, output_id: UUID, db: DB, who: Who) -> OutputOut:
    return service.recompose(db, who, project_id, output_id)


@router.post("/{output_id}/revise", response_model=OutputOut)
def revise(project_id: UUID, output_id: UUID, data: ReviseIn, db: DB, who: Who) -> OutputOut:
    return service.revise(db, who, project_id, output_id, data)


@router.patch("/{output_id}", response_model=OutputOut)
def update_settings(project_id: UUID, output_id: UUID, data: SettingsIn, db: DB, who: Who) -> OutputOut:
    return service.update_settings(db, who, project_id, output_id, data)


@router.post("/{output_id}/versions/{version_id}/approve", response_model=ApproveOut)
def approve(project_id: UUID, output_id: UUID, version_id: UUID, data: ApproveIn, db: DB, who: Who) -> ApproveOut:
    return service.approve(db, who, project_id, output_id, version_id, data)
