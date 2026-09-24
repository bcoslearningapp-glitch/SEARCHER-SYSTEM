"""Decisions: AI recommends, humans decide; resolved decisions are immutable (FR-DEC-001/002)."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit import service
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord, AIRecommendation, DecisionResolve
from tests.contract_helpers import as_contract


def _project(client: TestClient) -> str:
    body = {"title": "Decisions", "initial_input": "x", "input_type": "IDEA"}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _decision(client: TestClient, pid: str, **extra: object) -> dict[str, object]:
    body = {"question": "Interviews or survey first?", "options": ["interviews", "survey"], "blocking": True, **extra}
    response = client.post(f"/api/v1/projects/{pid}/decisions", json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


def test_ai_recommends_but_cannot_decide(client: TestClient, session: Session) -> None:
    pid = _project(client)
    decision = _decision(client, pid)
    ai = ai_principal("orchestrator")
    action = AIActionRecord(provider="mock", model="mock-1", template_version="t@1", timestamp=datetime.now(UTC))
    recommended = service.recommend_decision(
        session,
        ai,
        UUID(pid),
        UUID(str(decision["id"])),
        AIRecommendation(option="survey", rationale="cheaper", ai_action=action),
    )
    assert recommended.ai_recommendation is not None
    assert recommended.status.value == "OPEN"

    with pytest.raises(PolicyViolationError):
        service.resolve_decision(
            session,
            ai,
            UUID(pid),
            UUID(str(decision["id"])),
            DecisionResolve(final_decision="survey", human_justification="x"),
        )

    resolved = client.post(
        f"/api/v1/projects/{pid}/decisions/{decision['id']}/resolve",
        json={"final_decision": "interviews", "human_justification": "Richer causal signal"},
    ).json()
    assert resolved["status"] == "DECIDED"
    assert resolved["final_decision"] == "interviews"
    assert resolved["ai_recommendation"]["option"] == "survey", "AI recommendation stays distinct"
    assert contract_errors("framing.Decision", as_contract(resolved, drop=frozenset({"created_at"}))) == []


def test_resolved_decisions_are_immutable(client: TestClient, session: Session) -> None:
    pid = _project(client)
    decision = _decision(client, pid)
    client.post(
        f"/api/v1/projects/{pid}/decisions/{decision['id']}/resolve",
        json={"final_decision": "survey", "human_justification": "Faster"},
    )
    again = client.post(
        f"/api/v1/projects/{pid}/decisions/{decision['id']}/resolve",
        json={"final_decision": "interviews", "human_justification": "Changed mind"},
    )
    assert again.status_code == 409
    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(text("UPDATE decisions SET final_decision = 'x' WHERE id = :id"), {"id": decision["id"]})


def test_degraded_decision_mode_requires_disclosure(client: TestClient) -> None:
    pid = _project(client)
    decision = _decision(client, pid)
    url = f"/api/v1/projects/{pid}/decisions/{decision['id']}/resolve"
    missing = client.post(
        url, json={"final_decision": "survey", "human_justification": "Urgent", "incomplete_evidence": True}
    )
    assert missing.status_code == 422
    ok = client.post(
        url,
        json={
            "final_decision": "survey",
            "human_justification": "Board meets tomorrow",
            "incomplete_evidence": True,
            "unverified": ["Response rates"],
            "risks": ["Low response bias"],
            "later_review": "Revisit after pilot",
        },
    ).json()
    assert ok["methodology_path"] == "DECISION_UNDER_INCOMPLETE_EVIDENCE"


def test_final_decision_must_be_an_option(client: TestClient) -> None:
    pid = _project(client)
    decision = _decision(client, pid)
    response = client.post(
        f"/api/v1/projects/{pid}/decisions/{decision['id']}/resolve",
        json={"final_decision": "something else", "human_justification": "x"},
    )
    assert response.status_code == 422


def test_open_decisions_appear_in_research_state(client: TestClient) -> None:
    pid = _project(client)
    decision = _decision(client, pid)
    state = client.get(f"/api/v1/projects/{pid}/research-state").json()
    assert state["pending_decision_ids"] == [decision["id"]]
