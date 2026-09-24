"""Source library and Hybrid Source Access HTTP API."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.enums import AccessResponseForm, SourceAccessRequestStatus
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.sources_library import service
from research_api.modules.sources_library.schemas import (
    AccessRequestIn,
    AccessRequestOut,
    AccessResponseOut,
    AssetOut,
    CancelIn,
    CatalogIn,
    EditionOut,
    ExcerptOut,
    PageExcerptIn,
    ReverifyIn,
    SearchResponse,
    SourceLeadIn,
    SourceLeadOut,
    SourceLeadVerifyIn,
    TextResponseIn,
    WorkOut,
)
from research_api.platform import queue
from research_api.platform.db import get_session
from research_api.platform.storage import TooLargeError

logger = logging.getLogger(__name__)

library = APIRouter(prefix="/api/v1/sources", tags=["sources"])
project_sources = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["sources"])

DB = Annotated[Session, Depends(get_session)]
Who = Annotated[Principal, Depends(current_principal)]


async def _read_limited(upload: UploadFile) -> bytes:
    limit = get_settings().max_upload_bytes
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise TooLargeError(f"upload exceeds {limit} bytes", limit=limit)
    return data


def _dispatch_ingestion(db: Session, asset_id: UUID, job_id: UUID | None) -> None:
    """Dispatch only after the asset and job are committed, so the worker can see them."""
    if job_id is None:
        return
    db.commit()
    try:
        queue.dispatch(service.INGEST_TASK, job_id)
    except Exception as exc:
        logger.warning("ingestion dispatch failed for asset %s", asset_id, exc_info=True)
        service.record_dispatch_failure(db, asset_id, job_id, str(exc))
        db.commit()


@library.post("", response_model=WorkOut, status_code=status.HTTP_201_CREATED)
def catalog(data: CatalogIn, db: DB, who: Who) -> WorkOut:
    return service.catalog(db, who, data)


@library.get("", response_model=list[WorkOut])
def list_works(db: DB, project_id: UUID | None = None) -> list[WorkOut]:
    return service.list_works(db, project_id=project_id)


@library.get("/search", response_model=SearchResponse)
def search(
    db: DB, q: Annotated[str, Query(min_length=1, max_length=500)], project_id: UUID | None = None, limit: int = 20
) -> SearchResponse:
    return service.search(db, q, project_id=project_id, limit=min(max(limit, 1), 100))


@library.get("/works/{work_id}", response_model=WorkOut)
def get_work(work_id: UUID, db: DB) -> WorkOut:
    return service.get_work(db, work_id)


@library.get("/editions/{edition_id}", response_model=EditionOut)
def get_edition(edition_id: UUID, db: DB) -> EditionOut:
    return service.get_edition(db, edition_id)


@library.post("/editions/{edition_id}/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
async def upload_asset(edition_id: UUID, db: DB, who: Who, file: Annotated[UploadFile, File()]) -> AssetOut:
    data = await _read_limited(file)
    asset, job_id = service.upload_asset(db, who, edition_id, data, file.filename)
    _dispatch_ingestion(db, asset.id, job_id)
    return service.get_asset(db, asset.id)


@library.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: UUID, db: DB) -> AssetOut:
    return service.get_asset(db, asset_id)


@library.post("/assets/{asset_id}/excerpts", response_model=ExcerptOut, status_code=status.HTTP_201_CREATED)
def create_page_excerpt(asset_id: UUID, data: PageExcerptIn, db: DB, who: Who) -> ExcerptOut:
    return service.create_page_excerpt(db, who, asset_id, data)


@library.get("/excerpts/{excerpt_id}", response_model=ExcerptOut)
def get_excerpt(excerpt_id: UUID, db: DB) -> ExcerptOut:
    return service.get_excerpt(db, excerpt_id)


@library.post("/editions/{edition_id}/reverify", response_model=EditionOut)
def reverify(edition_id: UUID, data: ReverifyIn, db: DB, who: Who) -> EditionOut:
    return service.reverify_edition(db, who, edition_id, data)


@library.get("/editions/{edition_id}/excerpts", response_model=list[ExcerptOut])
def list_excerpts(edition_id: UUID, db: DB) -> list[ExcerptOut]:
    return service.list_excerpts(db, edition_id)


@project_sources.post("/sources/{work_id}", response_model=WorkOut)
def link(project_id: UUID, work_id: UUID, db: DB, who: Who) -> WorkOut:
    return service.link_to_project(db, who, project_id, work_id)


@project_sources.get("/access-requests", response_model=list[AccessRequestOut])
def list_access_requests(
    project_id: UUID, db: DB, status: SourceAccessRequestStatus | None = None
) -> list[AccessRequestOut]:
    return service.list_access_requests(db, project_id, status=status)


@project_sources.post("/access-requests", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def create_access_request(project_id: UUID, data: AccessRequestIn, db: DB, who: Who) -> AccessRequestOut:
    return service.create_access_request(db, who, project_id, data)


@project_sources.post("/access-requests/{request_id}/responses", response_model=AccessResponseOut)
def respond_text(project_id: UUID, request_id: UUID, data: TextResponseIn, db: DB, who: Who) -> AccessResponseOut:
    return service.respond_with_text(db, who, project_id, request_id, data)


@project_sources.post("/access-requests/{request_id}/responses/file", response_model=AccessResponseOut)
async def respond_file(
    project_id: UUID,
    request_id: UUID,
    db: DB,
    who: Who,
    file: Annotated[UploadFile, File()],
    form: Annotated[AccessResponseForm, Form()],
    fulfills_request: Annotated[bool, Form()] = False,
) -> AccessResponseOut:
    data = await _read_limited(file)
    response, job_id = service.respond_with_file(
        db, who, project_id, request_id, form=form, data=data, filename=file.filename, fulfills=fulfills_request
    )
    if response.asset is not None:
        _dispatch_ingestion(db, response.asset.id, job_id)
        response.asset = service.get_asset(db, response.asset.id)
    return response


@project_sources.post("/access-requests/{request_id}/cancel", response_model=AccessRequestOut)
def cancel(project_id: UUID, request_id: UUID, data: CancelIn, db: DB, who: Who) -> AccessRequestOut:
    return service.cancel_access_request(db, who, project_id, request_id, data.reason)


@project_sources.get("/source-leads", response_model=list[SourceLeadOut])
def list_leads(project_id: UUID, db: DB) -> list[SourceLeadOut]:
    return service.list_leads(db, project_id)


@project_sources.post("/source-leads", response_model=SourceLeadOut, status_code=status.HTTP_201_CREATED)
def create_lead(project_id: UUID, data: SourceLeadIn, db: DB, who: Who) -> SourceLeadOut:
    return service.create_lead(db, who, project_id, data)


@project_sources.post("/source-leads/{lead_id}/verify", response_model=SourceLeadOut)
def verify_lead(project_id: UUID, lead_id: UUID, data: SourceLeadVerifyIn, db: DB, who: Who) -> SourceLeadOut:
    return service.verify_lead(db, who, project_id, lead_id, data.excerpt_id)


@project_sources.post("/source-leads/{lead_id}/discard", response_model=SourceLeadOut)
def discard_lead(project_id: UUID, lead_id: UUID, data: CancelIn, db: DB, who: Who) -> SourceLeadOut:
    return service.discard_lead(db, who, project_id, lead_id, data.reason)
