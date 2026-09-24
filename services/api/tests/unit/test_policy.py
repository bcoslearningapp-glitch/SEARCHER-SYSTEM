import pytest

from research_api.contracts.enums import ActorKind, ActorRole
from research_api.modules.governance_audit.policy import POLICIES, PolicyViolationError, authorize, evaluate
from research_api.modules.governance_audit.principal import Principal, ai_principal, local_owner, system_principal

OWNER = local_owner()
AI = ai_principal("orchestrator")
SYSTEM = system_principal("worker")


def test_local_owner_holds_every_human_role() -> None:
    assert OWNER.kind is ActorKind.HUMAN
    assert {ActorRole.RESEARCHER, ActorRole.CONSTITUTIONAL_AUTHORITY} <= OWNER.roles


@pytest.mark.parametrize("action", [a for a, p in POLICIES.items() if p.human_only_approval])
def test_ai_can_never_perform_approval_actions(action: str) -> None:
    decision = evaluate(AI, action)
    assert not decision.allowed
    assert not decision.requires_approval


def test_ai_request_approval_actions_are_not_executed_directly() -> None:
    decision = evaluate(AI, "note.capture")
    assert not decision.allowed
    assert decision.requires_approval


def test_ai_act_and_notify_is_allowed_with_notification() -> None:
    decision = evaluate(AI, "problem_frame.draft")
    assert decision.allowed and decision.notify


def test_unregistered_actions_are_denied_for_everyone() -> None:
    for principal in (OWNER, AI, SYSTEM):
        assert not evaluate(principal, "database.drop_everything").allowed


def test_human_without_required_role_is_denied() -> None:
    researcher_only = Principal(ActorKind.HUMAN, "r1", frozenset({ActorRole.RESEARCHER}))
    with pytest.raises(PolicyViolationError, match="CONSTITUTIONAL_AUTHORITY"):
        authorize(researcher_only, "source.catalog_foundational")


def test_system_limited_to_system_actions() -> None:
    assert evaluate(SYSTEM, "project.transition").allowed
    assert not evaluate(SYSTEM, "problem_frame.approve").allowed


def test_acting_role_is_recorded_for_humans() -> None:
    assert authorize(OWNER, "problem_frame.approve").acting_role is ActorRole.RESEARCHER
    assert authorize(OWNER, "source.catalog_foundational").acting_role is ActorRole.CONSTITUTIONAL_AUTHORITY
