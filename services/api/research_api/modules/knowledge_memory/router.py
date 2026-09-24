"""Knowledge memory HTTP API (PRD §28-29, §35)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.knowledge_memory import service
from research_api.modules.knowledge_memory.schemas import (
    KnowledgeIn,
    KnowledgeOut,
    KnowledgeRevision,
    PromoteIn,
    PromoteOut,
    ReuseIn,
    ReuseOut,
    StandingIn,
    VersionOut,
)
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["knowledge"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/knowledge", response_model=list[KnowledgeOut])
def list_items(project_id: UUID, db: DB) -> list[KnowledgeOut]:
    return service.list_items(db, project_id)


@router.post("/knowledge", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
def create_item(project_id: UUID, data: KnowledgeIn, db: DB, who: Who) -> KnowledgeOut:
    return service.create_item(db, who, project_id, data)


@router.get("/knowledge/{item_id}", response_model=KnowledgeOut)
def get_item(project_id: UUID, item_id: UUID, db: DB) -> KnowledgeOut:
    return service.get_item(db, project_id, item_id)


@router.get("/knowledge/{item_id}/versions", response_model=list[VersionOut])
def list_versions(project_id: UUID, item_id: UUID, db: DB) -> list[VersionOut]:
    return service.list_versions(db, project_id, item_id)


@router.post("/knowledge/{item_id}/revise", response_model=KnowledgeOut)
def revise_item(project_id: UUID, item_id: UUID, data: KnowledgeRevision, db: DB, who: Who) -> KnowledgeOut:
    return service.revise_item(db, who, project_id, item_id, data)


@router.post("/knowledge/{item_id}/promote", response_model=PromoteOut)
def promote(project_id: UUID, item_id: UUID, data: PromoteIn, db: DB, who: Who) -> PromoteOut:
    return service.promote(db, who, project_id, item_id, data)


@router.post("/knowledge/{item_id}/standing", response_model=KnowledgeOut)
def change_standing(project_id: UUID, item_id: UUID, data: StandingIn, db: DB, who: Who) -> KnowledgeOut:
    return service.change_standing(db, who, project_id, item_id, data)


@router.post("/knowledge/{item_id}/reuse", response_model=ReuseOut, status_code=status.HTTP_201_CREATED)
def reuse_item(project_id: UUID, item_id: UUID, data: ReuseIn, db: DB, who: Who) -> ReuseOut:
    return service.reuse_item(db, who, project_id, item_id, data)


@router.get("/reused-knowledge", response_model=list[ReuseOut])
def reused_in(project_id: UUID, db: DB) -> list[ReuseOut]:
    return service.reused_in(db, project_id)
