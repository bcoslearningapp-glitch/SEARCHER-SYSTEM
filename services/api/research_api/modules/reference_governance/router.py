"""Foundational library and reference review HTTP API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from research_api.config import get_settings
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.reference_governance import service
from research_api.modules.reference_governance.schemas import (
    ApproveIn,
    AyahOut,
    EntryIn,
    EntryOut,
    FoundationalOut,
    FoundationalStageIn,
    HadithIn,
    HadithOut,
    JudgmentIn,
    JudgmentOut,
    ReviewIn,
    ReviewOut,
)
from research_api.platform.db import DBSession
from research_api.platform.storage import TooLargeError

library = APIRouter(prefix="/api/v1/reference", tags=["reference"])
reviews = APIRouter(prefix="/api/v1/projects/{project_id}/reference-reviews", tags=["reference"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@library.get("/foundational-sources", response_model=list[FoundationalOut])
def list_foundational(db: DB) -> list[FoundationalOut]:
    return service.list_foundational(db)


@library.post("/foundational-sources", response_model=FoundationalOut, status_code=status.HTTP_201_CREATED)
def stage(data: FoundationalStageIn, db: DB, who: Who) -> FoundationalOut:
    return service.stage_foundational(db, who, data)


@library.post("/quran-datasets", response_model=FoundationalOut, status_code=status.HTTP_201_CREATED)
async def stage_quran(
    db: DB,
    who: Who,
    work_id: Annotated[UUID, Form()],
    edition_version: Annotated[str, Form(min_length=1)],
    file: Annotated[UploadFile, File()],
) -> FoundationalOut:
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise TooLargeError(f"upload exceeds {limit} bytes", limit=limit)
    return service.stage_quran_dataset(db, who, work_id, edition_version, data)


@library.post("/foundational-sources/{source_id}/approve", response_model=FoundationalOut)
def approve(source_id: UUID, data: ApproveIn, db: DB, who: Who) -> FoundationalOut:
    return service.approve_foundational(db, who, source_id, data)


@library.get("/quran/{surah}/{ayah}", response_model=list[AyahOut])
def quran(db: DB, surah: int, ayah: int, to: Annotated[int | None, Query(ge=1)] = None) -> list[AyahOut]:
    return service.get_ayat(db, surah, ayah, to)


@library.post("/foundational-sources/{source_id}/hadith", response_model=HadithOut, status_code=status.HTTP_201_CREATED)
def add_hadith(source_id: UUID, data: HadithIn, db: DB, who: Who) -> HadithOut:
    return service.add_hadith(db, who, source_id, data)


@library.get("/hadith/{record_id}", response_model=HadithOut)
def get_hadith(record_id: UUID, db: DB) -> HadithOut:
    return service.get_hadith(db, record_id)


@reviews.get("", response_model=list[ReviewOut])
def list_reviews(project_id: UUID, db: DB) -> list[ReviewOut]:
    return service.list_reviews(db, project_id)


@reviews.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(project_id: UUID, data: ReviewIn, db: DB, who: Who) -> ReviewOut:
    return service.create_review(db, who, project_id, data)


@reviews.get("/{review_id}", response_model=ReviewOut)
def get_review(project_id: UUID, review_id: UUID, db: DB) -> ReviewOut:
    return service.get_review(db, project_id, review_id)


@reviews.post("/{review_id}/entries", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def add_entry(project_id: UUID, review_id: UUID, data: EntryIn, db: DB, who: Who) -> EntryOut:
    return service.add_entry(db, who, project_id, review_id, data)


@reviews.post("/{review_id}/judgments", response_model=JudgmentOut, status_code=status.HTTP_201_CREATED)
def judge(project_id: UUID, review_id: UUID, data: JudgmentIn, db: DB, who: Who) -> JudgmentOut:
    return service.judge(db, who, project_id, review_id, data)
