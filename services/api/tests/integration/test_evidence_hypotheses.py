"""Evidence, exact quotes, lineage, counter-evidence tracks and hypotheses (issues #14, #15)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.contracts.schemas import contract_errors
from research_api.modules.claims_evidence import service as evidence_service
from research_api.modules.claims_evidence.schemas import AssessmentIn, EvidenceIn
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.modules.sources_library import ingestion
from research_api.platform import queue
from tests.contract_helpers import as_contract
from tests.pdf_fixtures import make_pdf

AI = ai_principal("orchestrator")
ACTION = AIActionRecord(provider="mock", model="mock-1", template_version="evidence@1", timestamp=datetime.now(UTC))
FORMULATED = {
    "statement": "Loss of mentoring drives year-two disengagement",
    "context": "Construction apprenticeships",
    "expected_outcome": "Cohorts that keep mentors retain engagement",
    "proposed_mechanism": "Mentors buffer workplace isolation",
    "falsification_conditions": ["Engagement drops equally where mentoring continues"],
}


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _project(client: TestClient) -> str:
    return str(
        client.post("/api/v1/projects", json={"title": "E", "initial_input": "x", "input_type": "HYPOTHESIS"}).json()[
            "id"
        ]
    )


def _excerpt(client: TestClient, pid: str, title: str, passage: str) -> tuple[str, str]:
    """Catalog a work and obtain a researcher-supplied exact excerpt. Returns (work_id, excerpt_id)."""
    work = client.post("/api/v1/sources", json={"work": {"title": title}, "project_id": pid}).json()
    request = client.post(
        f"/api/v1/projects/{pid}/access-requests",
        json={
            "edition_id": work["editions"][0]["id"],
            "reason": "evidence",
            "requested_scope": "p. 1",
            "acceptable_forms": ["EXACT_TEXT"],
        },
    ).json()
    response = client.post(
        f"/api/v1/projects/{pid}/access-requests/{request['id']}/responses",
        json={"form": "EXACT_TEXT", "location": "p. 1", "text": passage},
    ).json()
    return work["id"], response["excerpt"]["id"]


def _accept(
    client: TestClient, pid: str, target: tuple[str, str], role: str, excerpt: str, strength: str
) -> dict[str, Any]:
    proposed = client.post(
        f"/api/v1/projects/{pid}/evidence",
        json={
            "target_type": target[0],
            "target_id": target[1],
            "role": role,
            "finding": f"{role} finding",
            "excerpt_id": excerpt,
            "track": "CHALLENGE" if role == "CONTRADICTS" else "SUPPORT",
        },
    )
    assert proposed.status_code == 201, proposed.text
    accepted = client.post(
        f"/api/v1/projects/{pid}/evidence/{proposed.json()['id']}/assess",
        json={"decision": "ACCEPT", "strength": strength, "limitations": "single site"},
    )
    assert accepted.status_code == 200, accepted.text
    return dict(accepted.json())


def test_exact_quote_is_copied_from_the_source_span(client: TestClient, session: Session) -> None:
    work = client.post("/api/v1/sources", json={"work": {"title": "Study"}}).json()
    passage = "Mentoring declines sharply in the second year."
    asset = client.post(
        f"/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
        files={"file": ("s.pdf", make_pdf(["Intro.", passage]), "application/pdf")},
    ).json()
    ingestion.ingest_asset(session, UUID(asset["id"]))
    start = 0
    end = len("Mentoring declines sharply")
    ok = client.post(
        f"/api/v1/sources/assets/{asset['id']}/excerpts",
        json={"page_number": 2, "char_start": start, "char_end": end, "expected_text": "Mentoring declines sharply"},
    )
    assert ok.status_code == 201, ok.text
    excerpt = ok.json()
    assert excerpt["text"] == "Mentoring declines sharply"
    assert excerpt["verification_state"] == "MACHINE_VERIFIED"
    assert excerpt["is_exact_quote"] is True

    edited = client.post(
        f"/api/v1/sources/assets/{asset['id']}/excerpts",
        json={"page_number": 2, "char_start": start, "char_end": end, "expected_text": "Mentoring declines slightly"},
    )
    assert edited.status_code == 422, "a quote that differs from the source is refused"
    outside = client.post(
        f"/api/v1/sources/assets/{asset['id']}/excerpts", json={"page_number": 2, "char_start": 0, "char_end": 10_000}
    )
    assert outside.status_code == 422


def test_ai_proposes_evidence_but_only_humans_accept(client: TestClient, session: Session) -> None:
    pid = _project(client)
    claim = client.post(f"/api/v1/projects/{pid}/claims", json={"statement": "c", "claim_type": "CAUSAL_CLAIM"}).json()
    _, excerpt = _excerpt(client, pid, "Work A", "Passage A")
    candidate = evidence_service.propose_evidence(
        session,
        AI,
        UUID(pid),
        EvidenceIn(target_type="CLAIM", target_id=claim["id"], role="SUPPORTS", finding="f", excerpt_id=excerpt),
        ai_action=ACTION,
    )
    assert candidate.status.value == "CANDIDATE"
    assert candidate.provenance["kind"] == "AI_GENERATED"
    with pytest.raises(PolicyViolationError):
        evidence_service.assess_evidence(
            session, AI, UUID(pid), candidate.id, AssessmentIn(decision="ACCEPT", strength="STRONG")
        )
    no_strength = client.post(f"/api/v1/projects/{pid}/evidence/{candidate.id}/assess", json={"decision": "ACCEPT"})
    assert no_strength.status_code == 422


def test_claim_strength_follows_independent_evidence(client: TestClient) -> None:
    pid = _project(client)
    claim = client.post(f"/api/v1/projects/{pid}/claims", json={"statement": "c", "claim_type": "CAUSAL_CLAIM"}).json()
    target = ("CLAIM", claim["id"])
    work_a, ex_a = _excerpt(client, pid, "Original study", "A")
    accepted = _accept(client, pid, target, "SUPPORTS", ex_a, "STRONG")
    assert contract_errors("evidence.Evidence", as_contract(accepted, drop=frozenset({"created_at"}))) == []
    assert client.get(f"/api/v1/projects/{pid}/claims/{claim['id']}").json()["epistemic_strength"] == "PROMISING"

    work_b, ex_b = _excerpt(client, pid, "Summary article", "B")
    client.post(
        "/api/v1/sources/lineage", json={"from_work_id": work_b, "relation": "SUMMARIZES", "to_work_id": work_a}
    )
    _accept(client, pid, target, "SUPPORTS", ex_b, "STRONG")
    evidence_map = client.get(f"/api/v1/projects/{pid}/evidence-map/CLAIM/{claim['id']}").json()
    assert evidence_map["support_origins"] == 1, "a summary of the same study is not independent"
    assert client.get(f"/api/v1/projects/{pid}/claims/{claim['id']}").json()["epistemic_strength"] == "PROMISING"

    _, ex_c = _excerpt(client, pid, "Independent replication", "C")
    _accept(client, pid, target, "SUPPORTS", ex_c, "SUPPORTED")
    assert client.get(f"/api/v1/projects/{pid}/claims/{claim['id']}").json()["epistemic_strength"] == "STRONG"


def test_counter_evidence_tracks_distinguish_failure_from_absence(client: TestClient) -> None:
    pid = _project(client)
    h = client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "h"}}).json()
    body = {"target_type": "HYPOTHESIS", "target_id": h["id"], "scope": "Local library (en, ar)"}
    client.post(
        f"/api/v1/projects/{pid}/research-tracks",
        json={**body, "track": "CHALLENGE", "outcome": "RESEARCH_EXECUTION_FAILURE"},
    )
    tracks = client.get(f"/api/v1/projects/{pid}/evidence-map/HYPOTHESIS/{h['id']}").json()
    challenge = next(t for t in tracks["tracks"] if t["track"] == "CHALLENGE")
    assert challenge["execution_failed"] is True and challenge["searched"] is False
    assert tracks["counter_evidence_search_complete"] is False

    for track in ("CHALLENGE", "ALTERNATIVE_EXPLANATION"):
        client.post(
            f"/api/v1/projects/{pid}/research-tracks",
            json={**body, "track": track, "outcome": "NO_RELEVANT_EVIDENCE_FOUND"},
        )
    assert client.get(f"/api/v1/projects/{pid}/hypotheses/{h['id']}").json()["counter_evidence_search_complete"] is True


def test_scenario_d_hypothesis_challenge_downgrades_without_losing_history(
    client: TestClient, session: Session
) -> None:
    pid = _project(client)
    h = client.post(
        f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": FORMULATED["statement"]}}
    ).json()
    assert h["lifecycle_state"] == "IDEA" and h["epistemic_state"] == "UNRESOLVED"
    hid = h["id"]

    blocked = client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/transition",
        json={"target": "FORMULATED_HYPOTHESIS", "reason": "ready"},
    )
    assert blocked.status_code == 422
    client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/revise", json={"content": FORMULATED, "change_reason": "formulated"}
    )
    ok = client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/transition",
        json={"target": "FORMULATED_HYPOTHESIS", "reason": "ready"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["gate"]["result"] == "PASS_WITH_RESERVATIONS"  # no boundary conditions/assumptions yet

    target = ("HYPOTHESIS", hid)
    for title in ("Cohort study", "Regional survey"):
        _, ex = _excerpt(client, pid, title, title)
        _accept(client, pid, target, "SUPPORTS", ex, "SUPPORTED")
    current = client.get(f"/api/v1/projects/{pid}/hypotheses/{hid}").json()
    assert current["suggested_epistemic_state"] == "SUPPORTED"
    assert current["epistemic_state"] == "UNRESOLVED", "upgrades need a human assessment"
    client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/assess",
        json={"epistemic_state": "SUPPORTED", "reason": "two independent origins"},
    )

    # "Challenge this": counter-evidence arrives and is accepted.
    _, ex = _excerpt(client, pid, "Counter study", "Retention rose where mentoring was cut")
    _accept(client, pid, target, "CONTRADICTS", ex, "SUPPORTED")
    after = client.get(f"/api/v1/projects/{pid}/hypotheses/{hid}").json()
    assert after["epistemic_state"] == "CONTESTED", "new evidence downgrades earlier confidence"

    versions = client.get(f"/api/v1/projects/{pid}/hypotheses/{hid}/versions").json()
    states = [v["epistemic_state"] for v in versions]
    assert "SUPPORTED" in states and states[-1] == "CONTESTED", "history is preserved"
    assert versions[-1]["actor"]["kind"] == "SYSTEM"
    assert contract_errors("hypothesis.HypothesisVersion", as_contract(versions[-1])) == []
    events = [e["action"] for e in client.get("/api/v1/audit-events", params={"project_id": pid}).json()]
    assert "hypothesis.downgrade" in events

    # Design eligibility is blocked while contested and without counter-evidence search.
    for step in ("UNDER_REFERENCE_REVIEW", "UNDER_SCRUTINY", "UNDER_RESEARCH", "ASSESSED"):
        assert (
            client.post(
                f"/api/v1/projects/{pid}/hypotheses/{hid}/transition", json={"target": step, "reason": "progress"}
            ).status_code
            == 200
        )
    eligible = client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/transition", json={"target": "ELIGIBLE_FOR_DESIGN", "reason": "try"}
    )
    assert eligible.status_code == 422
    codes = {f["code"] for f in eligible.json()["error"]["details"]["findings"]}
    assert codes == {"epistemic.not_ready", "counter_evidence.missing"}

    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(
            text("UPDATE hypothesis_versions SET epistemic_state = 'SUPPORTED' WHERE hypothesis_id = :id"), {"id": hid}
        )


def test_assessed_evidence_is_immutable(client: TestClient, session: Session) -> None:
    pid = _project(client)
    claim = client.post(f"/api/v1/projects/{pid}/claims", json={"statement": "c", "claim_type": "OBSERVATION"}).json()
    _, ex = _excerpt(client, pid, "W", "P")
    accepted = _accept(client, pid, ("CLAIM", claim["id"]), "SUPPORTS", ex, "WEAK")
    again = client.post(f"/api/v1/projects/{pid}/evidence/{accepted['id']}/assess", json={"decision": "REJECT"})
    assert again.status_code == 409
    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(text("UPDATE evidence SET role = 'CONTRADICTS' WHERE id = :id"), {"id": accepted["id"]})


def test_mechanisms_are_first_class_and_linkable(client: TestClient) -> None:
    pid = _project(client)
    mechanism = client.post(
        f"/api/v1/projects/{pid}/mechanisms",
        json={"name": "Isolation buffering", "description": "Mentors reduce isolation"},
    ).json()
    assert mechanism["status"] == "PROPOSED"
    assert contract_errors("hypothesis.Mechanism", as_contract(mechanism, drop=frozenset({"created_at"}))) == []
    h1 = client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "h1"}}).json()
    h2 = client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "h2 (alternative)"}}).json()
    linked = client.post(
        f"/api/v1/projects/{pid}/hypotheses/{h1['id']}/mechanisms", json={"mechanism_id": mechanism["id"]}
    ).json()
    assert linked["mechanism_ids"] == [mechanism["id"]]
    competing = client.post(
        f"/api/v1/projects/{pid}/hypotheses/{h1['id']}/competing", json={"other_hypothesis_id": h2["id"]}
    ).json()
    assert competing["competing_hypothesis_ids"] == [h2["id"]]
    updated = client.patch(
        f"/api/v1/projects/{pid}/mechanisms/{mechanism['id']}",
        json={"status": "UNDER_INVESTIGATION", "reason": "evidence being gathered"},
    ).json()
    assert updated["status"] == "UNDER_INVESTIGATION"
    _, ex = _excerpt(client, pid, "Mech source", "M")
    _accept(client, pid, ("MECHANISM", mechanism["id"]), "SUPPORTS", ex, "WEAK")


def test_evidence_target_must_exist_in_project(client: TestClient) -> None:
    pid = _project(client)
    other = _project(client)
    claim = client.post(f"/api/v1/projects/{other}/claims", json={"statement": "c", "claim_type": "OBSERVATION"}).json()
    _, ex = _excerpt(client, pid, "W", "P")
    response = client.post(
        f"/api/v1/projects/{pid}/evidence",
        json={"target_type": "CLAIM", "target_id": claim["id"], "role": "SUPPORTS", "finding": "f", "excerpt_id": ex},
    )
    assert response.status_code == 404
