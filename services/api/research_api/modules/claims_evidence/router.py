"""Claims, assumptions and open questions HTTP API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from research_api.contracts.enums import EvidenceTargetType
from research_api.modules.claims_evidence import service
from research_api.modules.claims_evidence.schemas import (
    AssessmentIn,
    AssumptionIn,
    AssumptionOut,
    AssumptionReview,
    CaptureIn,
    ClaimIn,
    ClaimOut,
    ClaimUpdate,
    EvidenceIn,
    EvidenceMap,
    EvidenceOut,
    LineageIn,
    LineageOut,
    OpenQuestionClose,
    OpenQuestionIn,
    OpenQuestionOut,
    TrackRunIn,
    TrackRunOut,
)
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["claims"])

DB = DBSession
Who = Annotated[Principal, Depends(current_principal)]


@router.get("/claims", response_model=list[ClaimOut])
def list_claims(project_id: UUID, db: DB) -> list[ClaimOut]:
    return service.list_claims(db, project_id)


@router.post("/claims", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
def create_claim(project_id: UUID, data: ClaimIn, db: DB, who: Who) -> ClaimOut:
    return service.create_claim(db, who, project_id, data)


@router.get("/claims/{claim_id}", response_model=ClaimOut)
def get_claim(project_id: UUID, claim_id: UUID, db: DB) -> ClaimOut:
    return service.get_claim(db, project_id, claim_id)


@router.patch("/claims/{claim_id}", response_model=ClaimOut)
def update_claim(project_id: UUID, claim_id: UUID, data: ClaimUpdate, db: DB, who: Who) -> ClaimOut:
    return service.update_claim(db, who, project_id, claim_id, data)


@router.get("/assumptions", response_model=list[AssumptionOut])
def list_assumptions(project_id: UUID, db: DB) -> list[AssumptionOut]:
    return service.list_assumptions(db, project_id)


@router.post("/assumptions", response_model=AssumptionOut, status_code=status.HTTP_201_CREATED)
def create_assumption(project_id: UUID, data: AssumptionIn, db: DB, who: Who) -> AssumptionOut:
    return service.create_assumption(db, who, project_id, data)


@router.post("/assumptions/{assumption_id}/review", response_model=AssumptionOut)
def review_assumption(project_id: UUID, assumption_id: UUID, data: AssumptionReview, db: DB, who: Who) -> AssumptionOut:
    return service.review_assumption(db, who, project_id, assumption_id, data)


@router.get("/questions", response_model=list[OpenQuestionOut])
def list_questions(project_id: UUID, db: DB) -> list[OpenQuestionOut]:
    return service.list_questions(db, project_id)


@router.post("/questions", response_model=OpenQuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(project_id: UUID, data: OpenQuestionIn, db: DB, who: Who) -> OpenQuestionOut:
    return service.create_question(db, who, project_id, data)


@router.post("/questions/{question_id}/close", response_model=OpenQuestionOut)
def close_question(project_id: UUID, question_id: UUID, data: OpenQuestionClose, db: DB, who: Who) -> OpenQuestionOut:
    return service.close_question(db, who, project_id, question_id, data)


@router.post(
    "/notes/{note_id}/capture-as",
    response_model=ClaimOut | AssumptionOut | OpenQuestionOut,
    status_code=status.HTTP_201_CREATED,
)
def capture_note(
    project_id: UUID, note_id: UUID, data: CaptureIn, db: DB, who: Who
) -> ClaimOut | AssumptionOut | OpenQuestionOut:
    return service.capture_note(db, who, project_id, note_id, data)


@router.post("/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def propose_evidence(project_id: UUID, data: EvidenceIn, db: DB, who: Who) -> EvidenceOut:
    return service.propose_evidence(db, who, project_id, data)


@router.post("/evidence/{evidence_id}/assess", response_model=EvidenceOut)
def assess_evidence(project_id: UUID, evidence_id: UUID, data: AssessmentIn, db: DB, who: Who) -> EvidenceOut:
    return service.assess_evidence(db, who, project_id, evidence_id, data)


@router.get("/evidence-map/{target_type}/{target_id}", response_model=EvidenceMap)
def evidence_map(project_id: UUID, target_type: EvidenceTargetType, target_id: UUID, db: DB) -> EvidenceMap:
    return service.evidence_map(db, project_id, target_type, target_id)


@router.post("/research-tracks", response_model=TrackRunOut, status_code=status.HTTP_201_CREATED)
def record_track_run(project_id: UUID, data: TrackRunIn, db: DB, who: Who) -> TrackRunOut:
    return service.record_track_run(db, who, project_id, data)


lineage_router = APIRouter(prefix="/api/v1/sources/lineage", tags=["evidence"])


@lineage_router.post("", response_model=LineageOut, status_code=status.HTTP_201_CREATED)
def add_lineage(data: LineageIn, db: DB, who: Who) -> LineageOut:
    return service.add_lineage(db, who, data)


@lineage_router.get("", response_model=list[LineageOut])
def list_lineage(db: DB, work_id: UUID | None = None) -> list[LineageOut]:
    return service.list_lineage(db, work_id)
