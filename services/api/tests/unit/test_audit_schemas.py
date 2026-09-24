from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from research_api.contracts.enums import ActorKind, ActorRole
from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit.schemas import (
    Actor,
    AIActionRecord,
    AuditEntry,
    AuditEventOut,
    ResearchEventEntry,
    VersionContext,
)

HUMAN = Actor(kind=ActorKind.HUMAN, id="local-owner", role=ActorRole.RESEARCHER)
AI = Actor(kind=ActorKind.AI, id="research-orchestrator")
AI_ACTION = AIActionRecord(
    provider="mock", model="mock-1", template_version="t@1", timestamp=datetime.now(UTC)
)


def test_ai_actor_requires_provenance() -> None:
    with pytest.raises(ValidationError, match="ai_action provenance"):
        AuditEntry(action="hypothesis.propose", actor=AI)
    AuditEntry(action="hypothesis.propose", actor=AI, ai_action=AI_ACTION)


@pytest.mark.parametrize("action", ["approve", "Problem.approve", "problem frame.approve", ""])
def test_action_must_be_dotted_snake_case(action: str) -> None:
    with pytest.raises(ValidationError):
        AuditEntry(action=action, actor=HUMAN)


@pytest.mark.parametrize("event_type", ["problem_frame_approved", "", "Problem Frame"])
def test_event_type_must_be_pascal_case(event_type: str) -> None:
    with pytest.raises(ValidationError):
        ResearchEventEntry(event_type=event_type, actor=HUMAN)


def _out(actor: Actor, ai_action: AIActionRecord | None) -> AuditEventOut:
    return AuditEventOut(
        id=uuid4(),
        project_id=uuid4(),
        action="problem_frame.approve",
        entity_type="ProblemFrame",
        entity_id=uuid4(),
        occurred_at=datetime.now(UTC),
        actor=actor,
        versions=VersionContext(
            core_schema_version="0.1.0", methodology_version="1.0.0", constitution_version="1.0.0"
        ),
        previous_state={"status": "DRAFT"},
        new_state={"status": "APPROVED"},
        reason=None,
        ai_action=ai_action,
    )


@pytest.mark.parametrize(("actor", "ai_action"), [(HUMAN, None), (AI, AI_ACTION)])
def test_serialized_audit_event_conforms_to_canonical_contract(
    actor: Actor, ai_action: AIActionRecord | None
) -> None:
    assert contract_errors("event.AuditEvent", _out(actor, ai_action).to_contract()) == []


def test_contract_rejects_ai_event_without_provenance() -> None:
    payload = _out(AI, AI_ACTION).to_contract()
    del payload["ai_action"]
    assert contract_errors("event.AuditEvent", payload)
