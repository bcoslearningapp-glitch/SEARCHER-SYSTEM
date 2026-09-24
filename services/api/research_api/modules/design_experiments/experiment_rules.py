"""Experiment workflow and Experiment Readiness Gate (Core §50-51, §60; PRD §33-34, §41). Pure and risk-aware."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from research_api.contracts.enums import ExperimentState as E
from research_api.contracts.enums import HumanImpactDimension, HumanImpactFinding, RiskLevel
from research_api.contracts.enums import QualityGateResult as G
from research_api.modules.governance_audit.schemas import GateFinding

FORWARD: dict[E, frozenset[E]] = {
    E.PROPOSED: frozenset({E.PROTOCOL_DEFINED}),
    E.PROTOCOL_DEFINED: frozenset({E.RISK_REVIEW, E.APPROVED}),
    E.RISK_REVIEW: frozenset({E.APPROVED, E.PROTOCOL_DEFINED}),
    E.APPROVED: frozenset({E.RUNNING}),
    E.RUNNING: frozenset({E.DATA_COLLECTION_COMPLETE}),
    E.DATA_COLLECTION_COMPLETE: frozenset({E.ANALYSIS}),
    E.ANALYSIS: frozenset({E.INTERPRETED}),
    E.INTERPRETED: frozenset({E.CLOSED}),
}
TERMINAL = frozenset({E.CLOSED, E.ABORTED, E.INVALIDATED})
# Stopping states need a reason; INVALIDATED means the test itself is unusable, not that the hypothesis failed.
STOPS = frozenset({E.PAUSED, E.ABORTED, E.INVALIDATED})
PROTOCOL_FIELDS = ("method", "sample", "data_collected", "analysis_plan", "success_criteria")
HIGH_RISK = frozenset({RiskLevel.L3_HIGH_IMPACT, RiskLevel.L4_CRITICAL})


def can_transition(current: E, target: E, *, affects_people: bool, paused_from: E | None = None) -> bool:
    if current in TERMINAL:
        return False
    if current is E.PAUSED:
        return target in {E.ABORTED, E.INVALIDATED} or target is paused_from
    if target in STOPS:
        return not (target is E.PAUSED and current in {E.PROPOSED, E.INTERPRETED})
    if affects_people and current is E.PROTOCOL_DEFINED and target is E.APPROVED:
        return False  # people affected: the human-impact review comes first (FR-HUMAN-001)
    return target in FORWARD.get(current, frozenset())


@dataclass
class ReadinessInput:
    target: E
    risk: RiskLevel
    affects_people: bool
    protocol: dict[str, str]
    failure_conditions: list[str]
    stop_conditions: list[str]
    side_effects: list[str]
    concept_status: str
    reference_result: G = G.PASS
    execution_ready: bool = True
    impact: dict[HumanImpactDimension, HumanImpactFinding] = field(default_factory=dict)
    unresolved_external_approvals: int = 0
    observations: int = 0
    results: int = 0
    interpretations: int = 0


Add = Callable[[str, G, str], None]


def _protocol(data: ReadinessInput, add: Add) -> None:
    missing = [f for f in PROTOCOL_FIELDS if not (data.protocol.get(f) or "").strip()]
    if missing:
        add("protocol.incomplete", G.BLOCKED, f"The protocol is missing: {', '.join(missing)}.")


def _approval(data: ReadinessInput, add: Add) -> None:
    _protocol(data, add)
    if not data.failure_conditions:
        add("hypothesis.no_failure_conditions", G.BLOCKED, "The design hypothesis states no failure conditions.")
    if not data.stop_conditions:
        add("hypothesis.no_stop_conditions", G.BLOCKED, "The design hypothesis states no stop conditions.")
    if not data.side_effects:
        add("hypothesis.no_side_effects", G.PASS_WITH_RESERVATIONS, "No possible side effects have been considered.")
    if data.concept_status in {"REJECTED", "WITHDRAWN"}:
        add("concept.closed", G.BLOCKED, f"The design concept is {data.concept_status}.")
    elif data.concept_status != "SELECTED":
        add("concept.not_selected", G.PASS_WITH_RESERVATIONS, "The design concept has not been selected yet.")
    if data.affects_people:
        _impact(data, add)
    if data.reference_result in {G.BLOCKED, G.NEEDS_HUMAN_DECISION}:
        add("reference.not_cleared", data.reference_result, f"Reference review is {data.reference_result.value}.")
    elif data.reference_result is G.PASS_WITH_RESERVATIONS:
        add(
            "reference.reservations",
            G.PASS_WITH_RESERVATIONS,
            "Reference review has reservations or has not been done.",
        )
    if data.unresolved_external_approvals:
        add(
            "operational.external_approval_pending",
            G.PASS_WITH_RESERVATIONS,
            f"{data.unresolved_external_approvals} external approval(s) pending; the experiment cannot run yet.",
        )


def _impact(data: ReadinessInput, add: Add) -> None:
    missing = [d.value for d in HumanImpactDimension if d not in data.impact]
    if missing:
        add(
            "impact.incomplete", G.BLOCKED, f"People are affected; the human-impact review lacks: {', '.join(missing)}."
        )
    concerns = [d.value for d, f in data.impact.items() if f is HumanImpactFinding.CONCERN]
    if concerns:
        severity = G.BLOCKED if data.risk is RiskLevel.L4_CRITICAL else G.NEEDS_HUMAN_DECISION
        add("impact.concern", severity, f"Open human-impact concerns: {', '.join(sorted(concerns))}.")


def _running(data: ReadinessInput, add: Add) -> None:
    if not data.execution_ready:
        add(
            "operational.constrained",
            G.BLOCKED,
            "Operational constraints (including pending external approvals) prevent running the experiment now.",
        )
    if data.reference_result is G.BLOCKED:
        add("reference.not_cleared", G.BLOCKED, "Reference review is BLOCKED.")


def evaluate(data: ReadinessInput) -> tuple[G, list[GateFinding]]:
    findings: list[GateFinding] = []

    def add(code: str, severity: G, message: str) -> None:
        findings.append(GateFinding(code=code, severity=severity, message=message))

    if data.target is E.PROTOCOL_DEFINED:
        _protocol(data, add)
    elif data.target is E.APPROVED:
        _approval(data, add)
    elif data.target is E.RUNNING:
        _running(data, add)
    elif data.target is E.DATA_COLLECTION_COMPLETE and not data.observations:
        add("observations.none", G.BLOCKED, "No observations have been recorded.")
    elif data.target is E.INTERPRETED and not (data.results and data.interpretations):
        add(
            "interpretation.missing",
            G.BLOCKED,
            "Interpreting needs at least one analysed result and one interpretation.",
        )
    for severity in (G.BLOCKED, G.NEEDS_HUMAN_DECISION, G.PASS_WITH_RESERVATIONS):
        if any(f.severity is severity for f in findings):
            return severity, findings
    return G.PASS, findings
