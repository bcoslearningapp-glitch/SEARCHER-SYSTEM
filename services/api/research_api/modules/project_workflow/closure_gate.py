"""Project Closure Gate (PRD §41, Core §60, §66). Pure and risk-aware."""

from __future__ import annotations

from dataclasses import dataclass

from research_api.contracts.enums import QualityGateResult as G
from research_api.contracts.enums import RiskLevel
from research_api.modules.governance_audit.schemas import GateFinding

HIGH_RISK = frozenset({RiskLevel.L3_HIGH_IMPACT, RiskLevel.L4_CRITICAL})


@dataclass(frozen=True)
class ClosureInput:
    risk: RiskLevel
    blocking_decisions: int
    open_decisions: int
    evidence_candidates: int
    experiments_in_progress: list[str]
    unresolved: int
    limitations: int
    reopen_triggers: int


def evaluate(data: ClosureInput) -> tuple[G, list[GateFinding]]:
    findings: list[GateFinding] = []
    high = data.risk in HIGH_RISK

    def add(code: str, severity: G, message: str) -> None:
        findings.append(GateFinding(code=code, severity=severity, message=message))

    if data.blocking_decisions:
        add("decisions.blocking", G.BLOCKED, f"{data.blocking_decisions} blocking decision(s) are still open.")
    if data.open_decisions:
        severity = G.NEEDS_HUMAN_DECISION if high else G.PASS_WITH_RESERVATIONS
        add("decisions.open", severity, f"{data.open_decisions} decision(s) are still open.")
    if data.experiments_in_progress:
        severity = G.BLOCKED if data.risk is RiskLevel.L4_CRITICAL else G.NEEDS_HUMAN_DECISION
        titles = ", ".join(data.experiments_in_progress[:5])
        add("experiments.in_progress", severity, f"Experiments not yet closed: {titles}.")
    if data.evidence_candidates:
        add(
            "evidence.unassessed",
            G.PASS_WITH_RESERVATIONS,
            f"{data.evidence_candidates} evidence candidate(s) were never assessed.",
        )
    if not data.limitations:
        severity = G.NEEDS_HUMAN_DECISION if high else G.PASS_WITH_RESERVATIONS
        add("record.no_limitations", severity, "The closure record names no limitations.")
    if data.unresolved and not data.reopen_triggers:
        add(
            "record.no_reopen_triggers",
            G.PASS_WITH_RESERVATIONS,
            "Unresolved matters are listed but nothing says what would reopen the project.",
        )
    for severity in (G.BLOCKED, G.NEEDS_HUMAN_DECISION, G.PASS_WITH_RESERVATIONS):
        if any(f.severity is severity for f in findings):
            return severity, findings
    return G.PASS, findings
