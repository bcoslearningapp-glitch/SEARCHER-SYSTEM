"""Reliability registry (PRD §52). Operational metrics come from the request log; evaluation
results are recorded append-only by the Methodology Steward or an automated golden run.
Recording a result never changes stored knowledge (FR-EVAL-001).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_api.modules.ai_gateway import service as gateway
from research_api.modules.ai_reliability.dimensions import DIMENSIONS
from research_api.modules.ai_reliability.models import AIEvaluation
from research_api.modules.ai_reliability.schemas import (
    DimensionOut,
    EvaluationIn,
    EvaluationOut,
    ModelStanding,
    OperationalRow,
    ReliabilityOut,
)
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import AuditEntry
from research_api.platform.errors import RuleViolationError


def record_evaluation(
    session: Session, principal: Principal, data: EvaluationIn, *, run_id: UUID | None = None
) -> EvaluationOut:
    auth = authorized(principal, "ai_evaluation.record")
    dimension = DIMENSIONS.get(data.dimension)
    if dimension is None:
        raise RuleViolationError("unknown evaluation dimension", dimension=data.dimension, known=sorted(DIMENSIONS))
    row = AIEvaluation(
        provider=data.provider,
        model=data.model,
        dimension=dimension.key,
        score=data.score,
        threshold=dimension.threshold,
        comparator=dimension.comparator,
        passed=dimension.passes(data.score),
        sample_size=data.sample_size,
        method=data.method,
        fixture_set=data.fixture_set,
        notes=data.notes,
        details=data.details,
        recorded_by=auth.actor.model_dump(mode="json", exclude_none=True),
        run_id=run_id,
    )
    session.add(row)
    session.flush()
    governance.record_audit(
        session,
        AuditEntry(
            action="ai_evaluation.record",
            entity_type="AIEvaluation",
            entity_id=row.id,
            actor=auth.actor,
            new_state={"model": data.model, "dimension": dimension.key, "score": data.score, "passed": row.passed},
        ),
    )
    return EvaluationOut.model_validate(row)


def _operational(session: Session) -> list[OperationalRow]:
    rows = []
    for r in gateway.usage_by_model(session):
        attempted = r["succeeded"] + r["invalid_output"]
        rows.append(
            OperationalRow(
                **{**r, "estimated_cost_usd": Decimal(r["estimated_cost_usd"])},
                structured_output_reliability=(r["succeeded"] / attempted) if attempted else None,
            )
        )
    return rows


def reliability(session: Session) -> ReliabilityOut:
    evaluations = list(session.scalars(select(AIEvaluation).order_by(AIEvaluation.created_at)))
    by_model: dict[tuple[str, str], dict[str, EvaluationOut]] = {}
    for evaluation in evaluations:  # later results replace earlier ones per dimension
        by_model.setdefault((evaluation.provider, evaluation.model), {})[evaluation.dimension] = (
            EvaluationOut.model_validate(evaluation)
        )
    blocking = [d.key for d in DIMENSIONS.values() if d.blocking]
    models = [
        ModelStanding(
            provider=provider,
            model=model,
            latest=latest,
            blocking_failures=[k for k in blocking if k in latest and not latest[k].passed],
            blocking_unevaluated=[k for k in blocking if k not in latest],
        )
        for (provider, model), latest in sorted(by_model.items())
    ]
    return ReliabilityOut(
        dimensions=[DimensionOut(**d.__dict__) for d in DIMENSIONS.values()],
        operational=_operational(session),
        models=models,
    )


def history(session: Session, provider: str, model: str) -> list[EvaluationOut]:
    rows = session.scalars(
        select(AIEvaluation)
        .where(AIEvaluation.provider == provider, AIEvaluation.model == model)
        .order_by(AIEvaluation.created_at.desc())
    )
    return [EvaluationOut.model_validate(r) for r in rows]
