"""Claims, assumptions and open questions (issue #11)."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from research_api.contracts.schemas import contract_errors
from research_api.modules.claims_evidence import service
from research_api.modules.claims_evidence.schemas import AssumptionIn, AssumptionReview, ClaimIn
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from tests.contract_helpers import as_contract

AI = ai_principal("orchestrator")
ACTION = AIActionRecord(
    provider="mock", model="mock-1", template_version="assumption-detect@1", timestamp=datetime.now(UTC)
)


def _project(client: TestClient) -> str:
    body = {"title": "Claims", "initial_input": "x", "input_type": "IDEA"}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def test_researcher_claim_starts_active_and_unsubstantiated(client: TestClient) -> None:
    pid = _project(client)
    claim = client.post(
        f"/api/v1/projects/{pid}/claims",
        json={"statement": "Mentoring declines after year one.", "claim_type": "CAUSAL_CLAIM", "important": True},
    ).json()
    assert claim["statement_origin"] == "RESEARCHER_STATED"
    assert claim["workflow_state"] == "ACTIVE"
    assert claim["epistemic_strength"] == "UNSUBSTANTIATED", "assertion never creates evidential strength"
    assert (
        contract_errors(
            "claims.Claim", as_contract(claim, drop=frozenset({"source_note_id", "created_at", "updated_at"}))
        )
        == []
    )


def test_ai_claims_and_assumptions_stay_labeled_until_human_review(client: TestClient, session: Session) -> None:
    pid = UUID(_project(client))
    claim = service.create_claim(
        session, AI, pid, ClaimIn(statement="Pay drives churn", claim_type="CAUSAL_CLAIM"), ai_action=ACTION
    )
    assert claim.statement_origin.value == "SYSTEM_INFERRED"
    assert claim.workflow_state.value == "PROPOSED"
    assert claim.provenance["kind"] == "AI_GENERATED"

    assumption = service.create_assumption(
        session, AI, pid, AssumptionIn(statement="Apprentices value mentoring"), ai_action=ACTION
    )
    assert assumption.origin.value == "SYSTEM_INFERRED"
    assert assumption.status.value == "UNCONFIRMED"
    assert contract_errors("claims.Assumption", assumption.to_contract()) == []

    with pytest.raises(PolicyViolationError):
        service.review_assumption(session, AI, pid, assumption.id, AssumptionReview(status="CONFIRMED"))

    reviewed = client.post(
        f"/api/v1/projects/{pid}/assumptions/{assumption.id}/review",
        json={"status": "RECLASSIFIED", "reclassify_as": "SOURCE_DERIVED", "criticality": "FOUNDATIONAL"},
    ).json()
    assert reviewed["status"] == "RECLASSIFIED"
    assert reviewed["origin"] == "SOURCE_DERIVED"
    assert reviewed["provenance"]["kind"] == "AI_GENERATED", "provenance history is not rewritten"
    again = client.post(f"/api/v1/projects/{pid}/assumptions/{assumption.id}/review", json={"status": "CONFIRMED"})
    assert again.status_code == 409


def test_database_refuses_unlabeled_ai_inferred_assumption(client: TestClient, session: Session) -> None:
    pid = _project(client)
    with pytest.raises(IntegrityError, match="inferred_is_ai"), session.begin_nested():
        session.execute(
            text(
                "INSERT INTO assumptions (id, project_id, statement, origin, criticality, status, provenance,"
                " created_at, updated_at) VALUES (gen_random_uuid(), :pid, 's', 'SYSTEM_INFERRED', 'LOW',"
                " 'UNCONFIRMED', '{\"kind\": \"HUMAN_INPUT\"}', now(), now())"
            ),
            {"pid": pid},
        )


def test_human_assumptions_are_explicit_and_confirmed(client: TestClient) -> None:
    pid = _project(client)
    assumption = client.post(
        f"/api/v1/projects/{pid}/assumptions", json={"statement": "Cohorts are comparable", "criticality": "HIGH"}
    ).json()
    assert assumption["origin"] == "EXPLICIT"
    assert assumption["status"] == "CONFIRMED"


def test_capture_note_into_claim_assumption_and_question(client: TestClient) -> None:
    pid = _project(client)
    notes = [
        client.post(f"/api/v1/projects/{pid}/notes", json={"body": body}).json()
        for body in ("Attendance drops in month 14", "Supervisors change in year two", "Does pay matter?")
    ]
    claim = client.post(
        f"/api/v1/projects/{pid}/notes/{notes[0]['id']}/capture-as", json={"as": "claim", "claim_type": "OBSERVATION"}
    ).json()
    assert claim["statement"] == "Attendance drops in month 14"
    assert claim["provenance"]["derived_from"] == [notes[0]["id"]]
    assumption = client.post(
        f"/api/v1/projects/{pid}/notes/{notes[1]['id']}/capture-as", json={"as": "assumption"}
    ).json()
    assert assumption["origin"] == "EXPLICIT"
    question = client.post(
        f"/api/v1/projects/{pid}/notes/{notes[2]['id']}/capture-as",
        json={"as": "open_question", "question_type": "EMPIRICAL"},
    ).json()
    assert question["status"] == "OPEN"

    captured = {n["id"]: n["captured_as"] for n in client.get(f"/api/v1/projects/{pid}/notes").json()}
    assert captured[notes[0]["id"]] == "claim"
    twice = client.post(f"/api/v1/projects/{pid}/notes/{notes[0]['id']}/capture-as", json={"as": "claim"})
    assert twice.status_code == 409


def test_unknown_is_a_valid_conclusion(client: TestClient) -> None:
    pid = _project(client)
    q = client.post(f"/api/v1/projects/{pid}/questions", json={"question": "Why?", "question_type": "MECHANISM"}).json()
    closed = client.post(
        f"/api/v1/projects/{pid}/questions/{q['id']}/close",
        json={"status": "CLOSED_UNANSWERED", "conclusion": "INSUFFICIENT_EVIDENCE"},
    ).json()
    assert closed["conclusion"] == "INSUFFICIENT_EVIDENCE"
