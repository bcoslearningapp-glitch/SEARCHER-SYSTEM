"""Terminology and translation-integrity HTTP API (PRD §36)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.contracts.enums import TermStatus
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.knowledge_memory import terminology as service
from research_api.modules.knowledge_memory.terminology_schemas import (
    TermDecision,
    TermIn,
    TermOut,
    TermRevision,
    TranslationCheckIn,
    TranslationCheckOut,
)
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1", tags=["terminology"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/terminology", response_model=list[TermOut])
def list_terms(
    db: DB, domain: str | None = None, status: TermStatus | None = None, include_history: bool = False
) -> list[TermOut]:
    return service.list_terms(db, domain=domain, status=status, include_history=include_history)


@router.post("/terminology", response_model=TermOut, status_code=status.HTTP_201_CREATED)
def propose_term(data: TermIn, db: DB, who: Who) -> TermOut:
    return service.propose_term(db, who, data)


@router.get("/terminology/{term_id}/history", response_model=list[TermOut])
def term_history(term_id: UUID, db: DB) -> list[TermOut]:
    return service.term_history(db, term_id)


@router.post("/terminology/{term_id}/revise", response_model=TermOut, status_code=status.HTTP_201_CREATED)
def revise_term(term_id: UUID, data: TermRevision, db: DB, who: Who) -> TermOut:
    return service.revise_term(db, who, term_id, data)


@router.post("/terminology/{term_id}/approve", response_model=TermOut)
def approve_term(term_id: UUID, data: TermDecision, db: DB, who: Who) -> TermOut:
    return service.approve_term(db, who, term_id, data)


@router.post("/terminology/{term_id}/reject", response_model=TermOut)
def reject_term(term_id: UUID, data: TermDecision, db: DB, who: Who) -> TermOut:
    return service.reject_term(db, who, term_id, data)


@router.post("/integrity/translation-check", response_model=TranslationCheckOut)
def check_translation(data: TranslationCheckIn, db: DB) -> TranslationCheckOut:
    return service.check_translation(db, data)
