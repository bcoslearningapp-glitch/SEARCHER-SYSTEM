"""Portability HTTP API (PRD §45)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from research_api.config import get_settings
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.portability import package, service
from research_api.modules.portability.schemas import ImportOut
from research_api.platform.db import DBSession
from research_api.platform.errors import RuleViolationError

router = APIRouter(prefix="/api/v1", tags=["portability"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/projects/{project_id}/package")
def export_package(project_id: UUID, db: DB, who: Who) -> Response:
    data, package_id = service.export_project(db, who, project_id)
    return Response(
        data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="research-core-package-{package_id}.zip"'},
    )


@router.post("/packages/import", response_model=ImportOut, status_code=status.HTTP_201_CREATED)
async def import_package(db: DB, who: Who, file: Annotated[UploadFile, File()]) -> ImportOut:
    limit = min(package.MAX_PACKAGE_BYTES, max(get_settings().max_upload_bytes, 1))
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise RuleViolationError("package is larger than the upload limit")
    return service.import_project(db, who, data)
