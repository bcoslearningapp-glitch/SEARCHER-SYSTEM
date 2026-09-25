"""Cloud workspace HTTP API (PRD §56)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.modules.cloud_workspace import service
from research_api.modules.cloud_workspace.schemas import DeleteIn, PurgeOut, StageIn, StagingOut, WorkspaceInfoOut
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1", tags=["cloud-workspace"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/workspace", response_model=WorkspaceInfoOut)
def workspace_info() -> WorkspaceInfoOut:
    return service.info()


@router.post("/workspace/purge-expired", response_model=PurgeOut)
def purge_expired(db: DB, who: Who) -> PurgeOut:
    return service.purge_expired(db, who)


@router.get("/projects/{project_id}/workspace/stagings", response_model=list[StagingOut])
def list_stagings(project_id: UUID, db: DB) -> list[StagingOut]:
    return service.list_stagings(db, project_id)


@router.post(
    "/projects/{project_id}/workspace/stagings", response_model=StagingOut, status_code=status.HTTP_201_CREATED
)
def stage(project_id: UUID, body: StageIn, db: DB, who: Who) -> StagingOut:
    return service.stage(db, who, project_id, body)


@router.get("/projects/{project_id}/workspace/stagings/{staging_id}", response_model=StagingOut)
def get_staging(project_id: UUID, staging_id: UUID, db: DB) -> StagingOut:
    return service.get_staging(db, project_id, staging_id)


@router.post("/projects/{project_id}/workspace/stagings/{staging_id}/delete", response_model=StagingOut)
def delete_staging(project_id: UUID, staging_id: UUID, body: DeleteIn, db: DB, who: Who) -> StagingOut:
    return service.delete(db, who, project_id, staging_id, body.reason)
