"""Create -> frame -> approve, lifecycle, closure/reopen, fork, notes (issues #3, #4)."""

from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.contracts.schemas import contract_errors
from tests.contract_helpers import as_contract

COMPLETE_FRAME: dict[str, Any] = {
    "central_issue": "Year-two apprentice disengagement",
    "current_state": "Attendance drops about 30% in year two",
    "desired_state": "Sustained engagement through completion",
    "gap": "Drivers of the drop are unknown",
    "current_explanations": ["Pay plateau"],
    "initial_hypotheses": ["Mentoring declines after year one"],
    "context": "Construction apprenticeships, three regional colleges",
    "constraints": ["No budget for new staff"],
    "known": ["Drop starts around month 14"],
    "unknowns": ["Role of pay progression"],
    "research_questions": ["What drives year-two disengagement?"],
    "reference_review_points": ["Just treatment of apprentices"],
}


def _create(client: TestClient, **overrides: Any) -> dict[str, Any]:
    body = {
        "title": "Apprentice engagement",
        "initial_input": "Why do apprentices disengage?",
        "input_type": "RAW_QUESTION",
    }
    body.update(overrides)
    response = client.post("/api/v1/projects", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _draft(client: TestClient, pid: str, content: dict[str, Any]) -> dict[str, Any]:
    response = client.put(f"/api/v1/projects/{pid}/problem-frames/draft", json={"content": content})
    assert response.status_code == 200, response.text
    return response.json()


def test_create_project_conforms_to_contract_and_starts_in_draft(client: TestClient) -> None:
    project = _create(client)
    assert project["status"] == "DRAFT"
    assert project["research_mode"] == "EXPLORATION"
    assert project["owner"]["kind"] == "HUMAN"
    assert contract_errors("project", as_contract(project)) == []

    state = client.get(f"/api/v1/projects/{project['id']}/research-state").json()
    assert state["current_question"] is None  # raw input is not a complete problem model
    assert "Problem Frame" in state["next_action"]
    assert contract_errors("framing.ResearchState", as_contract(state)) == []


def test_full_create_frame_approve_flow(client: TestClient) -> None:
    pid = _create(client)["id"]

    # Cannot enter active research without an approved frame.
    blocked = client.post(f"/api/v1/projects/{pid}/transition", json={"target": "FRAMING"})
    assert blocked.status_code == 200
    no_frame = client.post(f"/api/v1/projects/{pid}/transition", json={"target": "ACTIVE_RESEARCH"})
    assert no_frame.status_code == 422

    incomplete = _draft(client, pid, {"central_issue": "Disengagement"})
    rejected = client.post(f"/api/v1/projects/{pid}/problem-frames/{incomplete['id']}/approve", json={})
    assert rejected.status_code == 422
    assert rejected.json()["error"]["details"]["findings"]

    partial = _draft(client, pid, {**COMPLETE_FRAME, "constraints": []})
    assert partial["id"] == incomplete["id"], "a single open draft is revised in place"
    needs_ack = client.post(f"/api/v1/projects/{pid}/problem-frames/{partial['id']}/approve", json={})
    assert needs_ack.status_code == 422
    approval = client.post(
        f"/api/v1/projects/{pid}/problem-frames/{partial['id']}/approve",
        json={"acknowledge_reservations": True, "reason": "Constraints are unknown yet; revisit after interviews."},
    )
    assert approval.status_code == 200, approval.text
    body = approval.json()
    assert body["methodology_path"] == "OVERRIDDEN_WITH_REASON"
    assert body["approved_by"]["kind"] == "HUMAN"
    assert contract_errors("framing.Approval", as_contract(body)) == []

    project = client.get(f"/api/v1/projects/{pid}").json()
    assert project["status"] == "ACTIVE_RESEARCH"
    frame = client.get(f"/api/v1/projects/{pid}/problem-frames/{partial['id']}").json()
    assert frame["status"] == "APPROVED"
    assert contract_errors("framing.ProblemFrameVersion", ProblemFrameLike(frame)) == []

    state = client.get(f"/api/v1/projects/{pid}/research-state").json()
    assert state["current_question"] == "What drives year-two disengagement?"
    assert "Role of pay progression" in state["unresolved_items"]

    # Material change -> new version supersedes the baseline; history kept.
    v2 = _draft(client, pid, COMPLETE_FRAME)
    assert v2["version_number"] == 2
    assert v2["supersedes_version_id"] == partial["id"]
    ok = client.post(f"/api/v1/projects/{pid}/problem-frames/{v2['id']}/approve", json={})
    assert ok.status_code == 200
    assert ok.json()["methodology_path"] == "COMPLIANT"
    versions = {v["version_number"]: v["status"] for v in client.get(f"/api/v1/projects/{pid}/problem-frames").json()}
    assert versions == {1: "SUPERSEDED", 2: "APPROVED"}

    events = [e["action"] for e in client.get("/api/v1/audit-events", params={"project_id": pid}).json()]
    assert "problem_frame.approve" in events


def ProblemFrameLike(frame: dict[str, Any]) -> dict[str, Any]:  # noqa: N802 - mirrors to_contract
    data: dict[str, Any] = as_contract(frame, drop=frozenset({"updated_at"}))
    data["content"] = {k: v for k, v in data["content"].items() if v not in ("", [])}
    return data


def test_approved_frame_is_immutable_in_database(client: TestClient, session: Session) -> None:
    pid = _create(client)["id"]
    frame = _draft(client, pid, COMPLETE_FRAME)
    assert client.post(f"/api/v1/projects/{pid}/problem-frames/{frame['id']}/approve", json={}).status_code == 200
    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(
            text("UPDATE problem_frame_versions SET content = '{}'::jsonb WHERE id = :id"), {"id": frame["id"]}
        )
    with pytest.raises(DBAPIError, match="never deleted"), session.begin_nested():
        session.execute(text("DELETE FROM problem_frame_versions WHERE id = :id"), {"id": frame["id"]})


def test_approving_an_approved_version_conflicts(client: TestClient) -> None:
    pid = _create(client)["id"]
    frame = _draft(client, pid, COMPLETE_FRAME)
    client.post(f"/api/v1/projects/{pid}/problem-frames/{frame['id']}/approve", json={})
    again = client.post(f"/api/v1/projects/{pid}/problem-frames/{frame['id']}/approve", json={})
    assert again.status_code == 409


def test_high_risk_projects_block_incomplete_frames(client: TestClient) -> None:
    pid = _create(client, risk_level="L3_HIGH_IMPACT")["id"]
    frame = _draft(client, pid, {**COMPLETE_FRAME, "constraints": []})
    response = client.post(
        f"/api/v1/projects/{pid}/problem-frames/{frame['id']}/approve",
        json={"acknowledge_reservations": True, "reason": "try anyway"},
    )
    assert response.status_code == 422


def test_close_requires_dedicated_action_and_reopen_preserves_closure(client: TestClient) -> None:
    pid = _create(client)["id"]
    frame = _draft(client, pid, COMPLETE_FRAME)
    client.post(f"/api/v1/projects/{pid}/problem-frames/{frame['id']}/approve", json={})
    assert client.post(f"/api/v1/projects/{pid}/transition", json={"target": "READY_TO_CLOSE"}).status_code == 200
    generic = client.post(f"/api/v1/projects/{pid}/transition", json={"target": "CLOSED"})
    assert generic.status_code == 409

    closure = client.post(
        f"/api/v1/projects/{pid}/close",
        json={
            "closure_type": "JUSTIFIED_STOP",
            "resolved": ["Scoped the question"],
            "confidence_scope": "Low; pilot only",
        },
    )
    assert closure.status_code == 200, closure.text
    assert client.get(f"/api/v1/projects/{pid}").json()["status"] == "CLOSED"
    assert (
        client.put(f"/api/v1/projects/{pid}/problem-frames/draft", json={"content": COMPLETE_FRAME}).status_code == 409
    )

    reopened = client.post(f"/api/v1/projects/{pid}/reopen", json={"trigger": "New cohort data contradicts findings"})
    assert reopened.json()["status"] == "REOPENED"
    closures = client.get(f"/api/v1/projects/{pid}/closures").json()
    assert len(closures) == 1
    assert closures[0]["reopen_trigger"] == "New cohort data contradicts findings"
    assert closures[0]["record"]["resolved"] == ["Scoped the question"]
    state = client.get(f"/api/v1/projects/{pid}/research-state").json()
    assert any("Reopen trigger" in item for item in state["unresolved_items"])


def test_fork_keeps_lineage_and_leaves_source_untouched(client: TestClient) -> None:
    source = _create(client)
    fork = client.post(f"/api/v1/projects/{source['id']}/fork", json={"title": "Fork: rural colleges"}).json()
    assert fork["forked_from_project_id"] == source["id"]
    assert fork["status"] == "DRAFT"
    assert client.get(f"/api/v1/projects/{source['id']}").json()["title"] == source["title"]


def test_notes_are_not_promoted_until_explicit_capture(client: TestClient) -> None:
    pid = _create(client)["id"]
    note = client.post(f"/api/v1/projects/{pid}/notes", json={"body": "Maybe it's the commute?"}).json()
    assert client.get(f"/api/v1/projects/{pid}/research-state").json()["unresolved_items"] == []

    captured = client.post(f"/api/v1/projects/{pid}/notes/{note['id']}/capture", json={"target": "unresolved_item"})
    assert captured.json()["captured_as"] == "unresolved_item"
    assert client.get(f"/api/v1/projects/{pid}/research-state").json()["unresolved_items"] == [
        "Maybe it's the commute?"
    ]
    bad = client.post(f"/api/v1/projects/{pid}/notes/{note['id']}/capture", json={"target": "approved_claim"})
    assert bad.status_code == 422


def test_unknown_project_is_404(client: TestClient) -> None:
    assert client.get(f"/api/v1/projects/{UUID(int=0)}").status_code == 404
