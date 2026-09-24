"""Policy Engine v0: deterministic action authorization (PRD §49, Core §57, FR-ACTION-001).

Policy is code/config, never prompt text. Each registered action declares:
- the AI authorization class (AUTONOMOUS / ACT_AND_NOTIFY / REQUEST_APPROVAL / FORBIDDEN);
- which human roles may perform it directly;
- whether it is a formal approval, which only a human may ever perform
  (FR-APPROVAL-001, Core §58).

Unregistered actions are denied: new mutations must be registered explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

from research_api.contracts.enums import ActionAuthorizationClass as AuthClass
from research_api.contracts.enums import ActorKind, ActorRole
from research_api.modules.governance_audit.principal import Principal

R = ActorRole
ANY_HUMAN_ROLE = frozenset({R.RESEARCHER, R.PROJECT_LEAD, R.METHODOLOGY_STEWARD, R.CONSTITUTIONAL_AUTHORITY})
RESEARCH_ROLES = frozenset({R.RESEARCHER, R.PROJECT_LEAD})


@dataclass(frozen=True)
class ActionPolicy:
    action: str
    ai_class: AuthClass
    human_roles: frozenset[ActorRole]
    system_allowed: bool = False
    human_only_approval: bool = False


def _p(
    action: str,
    ai_class: AuthClass,
    roles: frozenset[ActorRole] = RESEARCH_ROLES,
    *,
    system: bool = False,
    approval: bool = False,
) -> ActionPolicy:
    return ActionPolicy(action, ai_class, roles, system, approval)


A = AuthClass
POLICIES: dict[str, ActionPolicy] = {
    p.action: p
    for p in [
        # Project workflow
        _p("project.create", A.FORBIDDEN),
        _p("project.update", A.REQUEST_APPROVAL),
        _p("project.transition", A.REQUEST_APPROVAL, system=True),
        _p("project.set_mode", A.ACT_AND_NOTIFY, system=True),
        _p("project.fork", A.FORBIDDEN),
        _p("project.close", A.FORBIDDEN, frozenset({R.RESEARCHER, R.PROJECT_LEAD}), approval=True),
        _p("project.reopen", A.FORBIDDEN, frozenset({R.RESEARCHER, R.PROJECT_LEAD}), approval=True),
        _p("research_state.update", A.ACT_AND_NOTIFY, system=True),
        # Scratch space: AI may suggest capture but never capture silently (FR-SCRATCH-003)
        _p("note.create", A.FORBIDDEN),
        _p("note.update", A.FORBIDDEN),
        _p("note.capture", A.REQUEST_APPROVAL),
        # Framing
        _p("problem_frame.draft", A.ACT_AND_NOTIFY),
        _p("problem_frame.approve", A.FORBIDDEN, approval=True),
        _p("quality_gate.evaluate", A.AUTONOMOUS, ANY_HUMAN_ROLE, system=True),
        # Decisions
        _p("decision.create", A.ACT_AND_NOTIFY, system=True),
        _p("decision.recommend", A.AUTONOMOUS),
        _p("decision.resolve", A.FORBIDDEN, ANY_HUMAN_ROLE, approval=True),
        _p("decision.withdraw", A.FORBIDDEN),
        # Claims, assumptions, questions (AI proposals are labeled and reviewable)
        _p("claim.create", A.ACT_AND_NOTIFY),
        _p("claim.update", A.REQUEST_APPROVAL),
        _p("assumption.create", A.ACT_AND_NOTIFY),
        _p("assumption.review", A.FORBIDDEN, approval=True),
        _p("open_question.create", A.ACT_AND_NOTIFY),
        _p("open_question.close", A.REQUEST_APPROVAL),
        # Evidence: AI may propose candidates; only humans accept or reject (Core §32-36)
        _p("evidence.propose", A.ACT_AND_NOTIFY),
        _p("evidence.assess", A.FORBIDDEN, approval=True),
        _p("research_track.record", A.ACT_AND_NOTIFY, system=True),
        # Hypotheses and mechanisms
        _p("hypothesis.create", A.ACT_AND_NOTIFY),
        _p("hypothesis.revise", A.ACT_AND_NOTIFY),
        _p("hypothesis.transition", A.REQUEST_APPROVAL),
        _p("hypothesis.assess", A.FORBIDDEN, approval=True),
        _p("hypothesis.downgrade", A.AUTONOMOUS, system=True),
        _p("hypothesis.link", A.ACT_AND_NOTIFY),
        _p("mechanism.create", A.ACT_AND_NOTIFY),
        _p("mechanism.update", A.REQUEST_APPROVAL),
        # Foundational library and reference review (PRD §18-21). AI never adopts or judges.
        _p("reference.stage_foundational", A.FORBIDDEN, frozenset({R.CONSTITUTIONAL_AUTHORITY})),
        _p("reference.approve_foundational", A.FORBIDDEN, frozenset({R.CONSTITUTIONAL_AUTHORITY}), approval=True),
        _p(
            "reference.enter_hadith", A.FORBIDDEN, frozenset({R.RESEARCHER, R.PROJECT_LEAD, R.CONSTITUTIONAL_AUTHORITY})
        ),
        _p("reference.review_create", A.ACT_AND_NOTIFY),
        _p("reference.entry_add", A.ACT_AND_NOTIFY),
        _p("reference.judge", A.FORBIDDEN, approval=True),
        # Operational reality (PRD §5.3)
        _p("operational.constraint_add", A.ACT_AND_NOTIFY),
        _p("operational.constraint_resolve", A.REQUEST_APPROVAL),
        # Sources
        _p("source.catalog", A.ACT_AND_NOTIFY),
        _p("source.catalog_foundational", A.FORBIDDEN, frozenset({R.CONSTITUTIONAL_AUTHORITY}), approval=True),
        _p("source.upload_asset", A.FORBIDDEN),
        _p("source.reverify", A.FORBIDDEN, approval=True),
        _p("source.ingest", A.AUTONOMOUS, system=True),
        _p("source_access_request.create", A.ACT_AND_NOTIFY),
        _p("source_access_request.respond", A.FORBIDDEN),
        _p("source_access_request.cancel", A.FORBIDDEN),
        _p("source.excerpt", A.ACT_AND_NOTIFY),
        _p("source.lineage", A.ACT_AND_NOTIFY),
        _p("source_lead.create", A.ACT_AND_NOTIFY),
        _p("source_lead.resolve", A.FORBIDDEN),
    ]
}


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    allowed: bool
    requires_approval: bool
    notify: bool
    acting_role: ActorRole | None
    reason: str


class PolicyViolationError(Exception):
    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


def evaluate(principal: Principal, action: str) -> PolicyDecision:
    policy = POLICIES.get(action)
    if policy is None:
        return PolicyDecision(action, False, False, False, None, f"action '{action}' is not registered")

    if principal.kind is ActorKind.HUMAN:
        role = next((r for r in _ROLE_PREFERENCE if r in principal.roles and r in policy.human_roles), None)
        if role is None:
            return PolicyDecision(action, False, False, False, None, f"'{action}' requires one of {_names(policy)}")
        return PolicyDecision(action, True, False, False, role, "human actor holds a permitted role")

    if principal.kind is ActorKind.SYSTEM:
        if policy.system_allowed:
            return PolicyDecision(action, True, False, False, ActorRole.SYSTEM, "system action")
        return PolicyDecision(action, False, False, False, None, f"system components may not perform '{action}'")

    # AI actor
    if policy.human_only_approval or policy.ai_class is AuthClass.FORBIDDEN:
        return PolicyDecision(action, False, False, False, None, f"AI may not perform '{action}'")
    if policy.ai_class is AuthClass.REQUEST_APPROVAL:
        return PolicyDecision(action, False, True, True, None, f"AI must request human approval for '{action}'")
    notify = policy.ai_class is AuthClass.ACT_AND_NOTIFY
    return PolicyDecision(action, True, False, notify, None, f"AI {policy.ai_class.value.lower()}")


def authorize(principal: Principal, action: str) -> PolicyDecision:
    """Evaluate and raise `PolicyViolationError` unless the action may proceed now."""
    decision = evaluate(principal, action)
    if not decision.allowed:
        raise PolicyViolationError(decision)
    return decision


# Deterministic role choice when a human holds several permitted roles.
_ROLE_PREFERENCE = (R.RESEARCHER, R.PROJECT_LEAD, R.METHODOLOGY_STEWARD, R.CONSTITUTIONAL_AUTHORITY)


def _names(policy: ActionPolicy) -> list[str]:
    return sorted(r.value for r in policy.human_roles)
