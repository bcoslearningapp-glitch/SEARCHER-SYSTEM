"""AI reliability registry HTTP API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from research_api.modules.ai_reliability import service
from research_api.modules.ai_reliability.schemas import EvaluationIn, EvaluationOut, ReliabilityOut
from research_api.modules.governance_audit.principal import Principal, current_principal
from research_api.platform.db import DBSession

router = APIRouter(prefix="/api/v1/ai/reliability", tags=["ai reliability"])

Who = Annotated[Principal, Depends(current_principal)]


@router.get("", response_model=ReliabilityOut)
def reliability(db: DBSession) -> ReliabilityOut:
    return service.reliability(db)


@router.get("/models/{provider}/{model}", response_model=list[EvaluationOut])
def history(provider: str, model: str, db: DBSession) -> list[EvaluationOut]:
    return service.history(db, provider, model)


@router.post("/evaluations", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
def record(data: EvaluationIn, db: DBSession, who: Who) -> EvaluationOut:
    return service.record_evaluation(db, who, data)
