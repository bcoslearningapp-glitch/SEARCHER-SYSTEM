"""Project workflow HTTP API. Routers only translate HTTP; rules live in the service."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.modules.governance_audit.schemas import ApprovalOut, GateEvaluationOut
from research_api.modules.project_workflow import service
from research_api.modules.project_workflow.schemas import (
    CloseRequest,
    ClosureOut,
    ForkRequest,
    ModeRequest,
    NoteCaptureTarget,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    ProblemFrameApproveIn,
    ProblemFrameDraftIn,
    ProblemFrameOut,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    ReopenRequest,
    ResearchStateOut,
    ResearchStateUpdate,
    TransitionRequest,
)
from research_api.platform.db import get_session

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

DB = Annotated[Session, Depends(get_session)]
Who = Annotated[Principal, Depends(current_principal)]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: DB, who: Who) -> ProjectOut:
    return service.create_project(db, who, data)


@router.get("", response_model=list[ProjectOut])
def list_projects(db: DB) -> list[ProjectOut]:
    return service.list_projects(db)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, db: DB) -> ProjectOut:
    return service.get_project(db, project_id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: UUID, data: ProjectUpdate, db: DB, who: Who) -> ProjectOut:
    return service.update_project(db, who, project_id, data)


@router.post("/{project_id}/transition", response_model=ProjectOut)
def transition(project_id: UUID, data: TransitionRequest, db: DB, who: Who) -> ProjectOut:
    return service.transition_project(db, who, project_id, data.target, data.reason)


@router.post("/{project_id}/mode", response_model=ProjectOut)
def set_mode(project_id: UUID, data: ModeRequest, db: DB, who: Who) -> ProjectOut:
    return service.set_mode(db, who, project_id, data.mode, data.reason)


@router.post("/{project_id}/fork", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def fork(project_id: UUID, data: ForkRequest, db: DB, who: Who) -> ProjectOut:
    return service.fork_project(db, who, project_id, data)


@router.post("/{project_id}/close", response_model=ClosureOut)
def close(project_id: UUID, data: CloseRequest, db: DB, who: Who) -> ClosureOut:
    return service.close_project(db, who, project_id, data)


@router.post("/{project_id}/reopen", response_model=ProjectOut)
def reopen(project_id: UUID, data: ReopenRequest, db: DB, who: Who) -> ProjectOut:
    return service.reopen_project(db, who, project_id, data)


@router.get("/{project_id}/closures", response_model=list[ClosureOut])
def closures(project_id: UUID, db: DB) -> list[ClosureOut]:
    return service.list_closures(db, project_id)


@router.get("/{project_id}/research-state", response_model=ResearchStateOut)
def research_state(project_id: UUID, db: DB) -> ResearchStateOut:
    return service.get_research_state(db, project_id)


@router.patch("/{project_id}/research-state", response_model=ResearchStateOut)
def update_research_state(project_id: UUID, data: ResearchStateUpdate, db: DB, who: Who) -> ResearchStateOut:
    return service.update_research_state(db, who, project_id, data)


@router.get("/{project_id}/notes", response_model=list[NoteOut])
def list_notes(project_id: UUID, db: DB) -> list[NoteOut]:
    return service.list_notes(db, project_id)


@router.post("/{project_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(project_id: UUID, data: NoteCreate, db: DB, who: Who) -> NoteOut:
    return service.create_note(db, who, project_id, data)


@router.put("/{project_id}/notes/{note_id}", response_model=NoteOut)
def update_note(project_id: UUID, note_id: UUID, data: NoteUpdate, db: DB, who: Who) -> NoteOut:
    return service.update_note(db, who, project_id, note_id, data)


@router.post("/{project_id}/notes/{note_id}/capture", response_model=NoteOut)
def capture_note(project_id: UUID, note_id: UUID, data: NoteCaptureTarget, db: DB, who: Who) -> NoteOut:
    return service.capture_note(db, who, project_id, note_id, data)


@router.get("/{project_id}/problem-frames", response_model=list[ProblemFrameOut])
def list_frames(project_id: UUID, db: DB) -> list[ProblemFrameOut]:
    return service.list_frames(db, project_id)


@router.put("/{project_id}/problem-frames/draft", response_model=ProblemFrameOut)
def save_draft(project_id: UUID, data: ProblemFrameDraftIn, db: DB, who: Who) -> ProblemFrameOut:
    return service.save_draft(db, who, project_id, data.content)


@router.get("/{project_id}/problem-frames/{version_id}", response_model=ProblemFrameOut)
def get_frame(project_id: UUID, version_id: UUID, db: DB) -> ProblemFrameOut:
    return service.get_frame(db, project_id, version_id)


@router.post("/{project_id}/problem-frames/{version_id}/gate", response_model=GateEvaluationOut)
def evaluate_gate(project_id: UUID, version_id: UUID, db: DB, who: Who) -> GateEvaluationOut:
    return service.evaluate_framing_gate(db, who, project_id, version_id)


@router.post("/{project_id}/problem-frames/{version_id}/approve", response_model=ApprovalOut)
def approve(project_id: UUID, version_id: UUID, data: ProblemFrameApproveIn, db: DB, who: Who) -> ApprovalOut:
    return service.approve_frame(db, who, project_id, version_id, data)
