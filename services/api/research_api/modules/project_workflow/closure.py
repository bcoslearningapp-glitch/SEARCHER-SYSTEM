"""Closing a project through the Project Closure Gate (PRD §41, Core §60, §66).

Reads other modules through their public services only. Kept apart from
project_workflow.service, which those modules import.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    DecisionStatus,
    MethodologyPathStatus,
    QualityGateResult,
    QualityGateType,
    RiskLevel,
)
from research_api.modules.claims_evidence import service as evidence
from research_api.modules.design_experiments import experiment_service as experiments
from research_api.modules.governance_audit import service as governance
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.governance_audit.schemas import GateEvaluationOut
from research_api.modules.project_workflow import closure_gate
from research_api.modules.project_workflow import service as projects
from research_api.modules.project_workflow.schemas import CloseRequest, ClosureOut
from research_api.platform.errors import RuleViolationError


def evaluate(session: Session, principal: Principal, project_id: UUID, data: CloseRequest) -> GateEvaluationOut:
    authorized(principal, "quality_gate.evaluate")
    project = projects.get_project(session, project_id)
    open_decisions = governance.list_decisions(session, project_id, status=DecisionStatus.OPEN)
    result, findings = closure_gate.evaluate(
        closure_gate.ClosureInput(
            risk=RiskLevel(project.risk_level),
            blocking_decisions=sum(d.blocking for d in open_decisions),
            open_decisions=sum(not d.blocking for d in open_decisions),
            evidence_candidates=evidence.count_candidates(session, project_id),
            experiments_in_progress=[e.title for e in experiments.experiments_in_progress(session, project_id)],
            unresolved=len(data.unresolved),
            limitations=len(data.limitations),
            reopen_triggers=len(data.reopen_triggers),
        )
    )
    return governance.record_gate_evaluation(
        session,
        gate=QualityGateType.PROJECT_CLOSURE,
        result=result,
        risk_level=RiskLevel(project.risk_level),
        findings=findings,
        project_id=project_id,
        subject_type="Project",
        subject_id=project_id,
    )


def close(session: Session, principal: Principal, project_id: UUID, data: CloseRequest) -> ClosureOut:
    authorized(principal, "project.close")
    gate = evaluate(session, principal, project_id, data)
    if gate.result is QualityGateResult.BLOCKED:
        raise RuleViolationError(
            "Project Closure Gate is BLOCKED",
            gate_evaluation_id=str(gate.id),
            findings=[f.model_dump(mode="json") for f in gate.findings if f.severity is QualityGateResult.BLOCKED],
        )
    path = MethodologyPathStatus.COMPLIANT
    if gate.result is QualityGateResult.NEEDS_HUMAN_DECISION:
        if not (data.acknowledge_reservations and data.override_reason):
            raise RuleViolationError(
                "Project Closure Gate needs a human decision: acknowledge the reservations and give a reason",
                gate_evaluation_id=str(gate.id),
                findings=[f.model_dump(mode="json") for f in gate.findings],
            )
        path = MethodologyPathStatus.OVERRIDDEN_WITH_REASON
    return projects.close_project(
        session, principal, project_id, data, gate_evaluation_id=gate.id, methodology_path=path
    )
