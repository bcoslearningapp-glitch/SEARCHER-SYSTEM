"""Design Readiness Gate (Core §60, PRD §41). Pure and risk-aware."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from research_api.contracts.enums import QualityGateResult as G
from research_api.contracts.enums import RiskLevel
from research_api.modules.governance_audit.schemas import GateFinding

HIGH_RISK = frozenset({RiskLevel.L3_HIGH_IMPACT, RiskLevel.L4_CRITICAL})


@dataclass(frozen=True)
class Requirement:
    series_id: UUID
    requirement_id: UUID
    priority: str  # MUST | SHOULD | COULD
    statement: str


@dataclass(frozen=True)
class Coverage:
    coverage: str  # MEETS | PARTIAL | NOT_ADDRESSED | CONFLICTS
    requirement_id: UUID  # the version that was judged


@dataclass
class DesignGateInput:
    concept_status: str
    risk: RiskLevel
    requirements: list[Requirement]
    unconfirmed_requirements: int
    coverage: dict[UUID, Coverage]
    hypotheses_eligible: dict[UUID, bool] = field(default_factory=dict)
    reference_result: G = G.PASS
    execution_ready: bool = True


Add = Callable[[str, G, str], None]


def _requirement_findings(data: DesignGateInput, add: Add, escalate: G) -> None:
    if not data.requirements:
        add("requirements.missing", G.BLOCKED, "Design Requirements must exist before serious design (FR-DESIGN-001).")
    if data.unconfirmed_requirements:
        add(
            "requirements.unconfirmed",
            G.PASS_WITH_RESERVATIONS,
            f"{data.unconfirmed_requirements} AI-proposed requirement(s) are not yet confirmed by a researcher.",
        )
    for req in data.requirements:
        covered = data.coverage.get(req.series_id)
        label = f"'{req.statement[:80]}'"
        if covered is None or covered.coverage == "NOT_ADDRESSED":
            if req.priority == "MUST":
                add("coverage.must_missing", G.BLOCKED, f"MUST requirement {label} is not addressed.")
            elif req.priority == "SHOULD":
                add(
                    "coverage.should_missing", G.PASS_WITH_RESERVATIONS, f"SHOULD requirement {label} is not addressed."
                )
            continue
        if covered.coverage == "CONFLICTS":
            severity = G.BLOCKED if req.priority == "MUST" else escalate
            add("coverage.conflict", severity, f"The concept conflicts with requirement {label}.")
        elif covered.coverage == "PARTIAL" and req.priority == "MUST":
            add("coverage.must_partial", escalate, f"MUST requirement {label} is only partly met.")
        if covered.requirement_id != req.requirement_id:
            add(
                "coverage.stale",
                G.PASS_WITH_RESERVATIONS,
                f"Requirement {label} was revised after coverage was judged.",
            )


def _context_findings(data: DesignGateInput, add: Add) -> None:
    if not data.hypotheses_eligible:
        add("hypotheses.none", G.PASS_WITH_RESERVATIONS, "The concept is not linked to any hypothesis it builds on.")
    for hypothesis_id, eligible in data.hypotheses_eligible.items():
        if not eligible:
            add(
                "hypotheses.not_eligible",
                G.BLOCKED,
                f"Hypothesis {hypothesis_id} has not passed the Hypothesis Gate to ELIGIBLE_FOR_DESIGN.",
            )
    # A governing reference rejection outranks effectiveness (Core §74.8).
    if data.reference_result in {G.BLOCKED, G.NEEDS_HUMAN_DECISION}:
        add(
            "reference.not_cleared",
            data.reference_result,
            f"Reference review of the concept is {data.reference_result.value}.",
        )
    elif data.reference_result is G.PASS_WITH_RESERVATIONS:
        add(
            "reference.reservations",
            G.PASS_WITH_RESERVATIONS,
            "Reference review has reservations or has not been done.",
        )
    if not data.execution_ready:
        add(
            "operational.constrained",
            G.PASS_WITH_RESERVATIONS,
            "Operational constraints currently prevent execution; design may continue, execution may not.",
        )


def evaluate(data: DesignGateInput) -> tuple[G, list[GateFinding]]:
    findings: list[GateFinding] = []

    def add(code: str, severity: G, message: str) -> None:
        findings.append(GateFinding(code=code, severity=severity, message=message))

    if data.concept_status in {"REJECTED", "WITHDRAWN"}:
        add(
            "concept.closed",
            G.BLOCKED,
            f"The concept is {data.concept_status}; it stays in history but cannot proceed.",
        )
    # Reservations that matter more on high-impact projects need a human decision there.
    escalate = G.NEEDS_HUMAN_DECISION if data.risk in HIGH_RISK else G.PASS_WITH_RESERVATIONS
    _requirement_findings(data, add, escalate)
    _context_findings(data, add)
    for severity in (G.BLOCKED, G.NEEDS_HUMAN_DECISION, G.PASS_WITH_RESERVATIONS):
        if any(f.severity is severity for f in findings):
            return severity, findings
    return G.PASS, findings
