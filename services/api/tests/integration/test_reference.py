"""Foundational library, Qur'an/Hadith integrity, reference review, operational constraints (issues #12, #13).

All Qur'an fixtures are synthetic placeholders: the system must never contain model-generated Qur'anic text.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.contracts.enums import ActorKind, ActorRole
from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import Principal, ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.modules.reference_governance import service as reference
from research_api.modules.reference_governance.schemas import ApproveIn, EntryIn
from research_api.platform import queue
from tests.contract_helpers import as_contract

DATASET_V1 = (
    "# synthetic test fixture - not Qur'anic text\n"
    "@surah|1|Placeholder Surah One\n"
    "1|1|PLACEHOLDER-V1-1-1 نص تجريبي\n"
    "1|2|PLACEHOLDER-V1-1-2\n"
    "1|3|PLACEHOLDER-V1-1-3\n"
).encode()
DATASET_V2 = DATASET_V1.replace(b"V1", b"V2")
AI = ai_principal("orchestrator")
ACTION = AIActionRecord(provider="mock", model="mock-1", template_version="ref@1", timestamp=datetime.now(UTC))


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _quran_work(client: TestClient) -> str:
    return str(
        client.post("/api/v1/sources", json={"work": {"title": "Qur'an (test)", "authority_layer": "QURAN"}}).json()[
            "id"
        ]
    )


def _stage(client: TestClient, work_id: str, data: bytes, version: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/reference/quran-datasets",
        data={"work_id": work_id, "edition_version": version},
        files={"file": ("quran.txt", data, "text/plain")},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def _approve(client: TestClient, source_id: str) -> dict[str, Any]:
    response = client.post(f"/api/v1/reference/foundational-sources/{source_id}/approve", json={"reason": "verified"})
    assert response.status_code == 200, response.text
    return dict(response.json())


@pytest.fixture
def approved_quran(client: TestClient) -> dict[str, Any]:
    staged = _stage(client, _quran_work(client), DATASET_V1, "test-v1")
    return _approve(client, staged["id"])


def test_quran_is_served_only_after_human_approval(client: TestClient, session: Session) -> None:
    staged = _stage(client, _quran_work(client), DATASET_V1, "test-v1")
    assert staged["status"] == "STAGED"
    assert staged["dataset_summary"] == {"surahs": 1, "ayat": 3, "format": "lines"}
    assert client.get("/api/v1/reference/quran/1/1").status_code == 404, "staged text is not served"

    for principal in (AI, Principal(ActorKind.HUMAN, "r", frozenset({ActorRole.RESEARCHER}))):
        with pytest.raises(PolicyViolationError):
            reference.approve_foundational(session, principal, UUID(staged["id"]), ApproveIn(reason="x"))

    approved = _approve(client, staged["id"])
    assert approved["approved_by"]["kind"] == "HUMAN"
    assert contract_errors("reference.FoundationalSource", approved_contract(approved)) == []

    [ayah] = client.get("/api/v1/reference/quran/1/1").json()
    assert ayah == {
        "surah_number": 1,
        "surah_name": "Placeholder Surah One",
        "ayah_number": 1,
        "text": "PLACEHOLDER-V1-1-1 نص تجريبي",
        "source_id": staged["id"],
        "source_version": "test-v1",
        "source_sha256": staged["sha256"],
    }
    assert contract_errors("reference.QuranAyah", ayah) == []
    assert [a["ayah_number"] for a in client.get("/api/v1/reference/quran/1/2?to=3").json()] == [2, 3]
    assert client.get("/api/v1/reference/quran/1/9").status_code == 404

    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("UPDATE quran_ayat SET text = 'edited' WHERE source_id = :id"), {"id": staged["id"]})


def approved_contract(source: dict[str, Any]) -> dict[str, Any]:
    return as_contract(source, drop=frozenset({"dataset_summary"}))


def test_approving_a_new_text_retires_the_previous_one(client: TestClient) -> None:
    work = _quran_work(client)
    first = _approve(client, _stage(client, work, DATASET_V1, "v1")["id"])
    _approve(client, _stage(client, work, DATASET_V2, "v2")["id"])
    statuses = {s["id"]: s["status"] for s in client.get("/api/v1/reference/foundational-sources").json()}
    assert statuses[first["id"]] == "RETIRED"
    assert client.get("/api/v1/reference/quran/1/1").json()[0]["text"].startswith("PLACEHOLDER-V2")


def test_malformed_dataset_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/reference/quran-datasets",
        data={"work_id": _quran_work(client), "edition_version": "bad"},
        files={"file": ("q.txt", b"@surah|1|S\n1|1|a\n1|3|gap\n", "text/plain")},
    )
    assert response.status_code == 422
    assert "contiguous" in response.json()["error"]["message"]


def test_hadith_records_keep_edition_numbering(client: TestClient) -> None:
    work = client.post(
        "/api/v1/sources", json={"work": {"title": "Collection (test)", "authority_layer": "SUNNAH"}}
    ).json()
    staged = client.post(
        "/api/v1/reference/foundational-sources",
        json={"work_id": work["id"], "edition_version": "ed-1", "sha256": "a" * 64},
    ).json()
    record = {
        "collection": "Test collection",
        "number": "12",
        "numbering_scheme": "Edition A",
        "exact_text": "PLACEHOLDER",
    }
    not_approved = client.post(f"/api/v1/reference/foundational-sources/{staged['id']}/hadith", json=record)
    assert not_approved.status_code == 422
    _approve(client, staged["id"])
    created = client.post(f"/api/v1/reference/foundational-sources/{staged['id']}/hadith", json=record)
    assert created.status_code == 201
    duplicate = client.post(f"/api/v1/reference/foundational-sources/{staged['id']}/hadith", json=record)
    assert duplicate.status_code == 409
    other_scheme = client.post(
        f"/api/v1/reference/foundational-sources/{staged['id']}/hadith",
        json={**record, "numbering_scheme": "Edition B"},
    )
    assert other_scheme.status_code == 201, "different editions may number differently"


def _hypothesis(client: TestClient, pid: str) -> str:
    return str(client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "h"}}).json()["id"])


def _project(client: TestClient, risk: str = "L1_EXPLORATORY") -> str:
    body = {"title": "Ref", "initial_input": "x", "input_type": "IDEA", "risk_level": risk}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _review(client: TestClient, pid: str, hid: str) -> str:
    response = client.post(
        f"/api/v1/projects/{pid}/reference-reviews",
        json={
            "target_type": "HYPOTHESIS",
            "target_id": hid,
            "question": "Is the incentive acceptable?",
            "analytical_category": "VALUES_AND_EVALUATIVE_STANDARDS",
        },
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def test_layers_stay_separate_and_source_text_is_copied(
    client: TestClient, session: Session, approved_quran: dict[str, Any]
) -> None:
    pid = _project(client)
    rid = _review(client, pid, _hypothesis(client, pid))

    with pytest.raises(Exception, match="SYSTEM_SYNTHESIS"):
        reference.add_entry(
            session,
            AI,
            UUID(pid),
            UUID(rid),
            EntryIn(layer="APPROVED_INTERPRETATION", content="AI claims this is approved"),
            ai_action=ACTION,
        )
    synthesis = reference.add_entry(
        session,
        AI,
        UUID(pid),
        UUID(rid),
        EntryIn(layer="SYSTEM_SYNTHESIS", content="Possible link to fairness"),
        ai_action=ACTION,
    )
    assert synthesis.provenance["kind"] == "AI_GENERATED"
    assert (
        contract_errors(
            "reference.ReferenceEntry", as_contract(synthesis.model_dump(mode="json"), drop=frozenset({"created_at"}))
        )
        == []
    )

    entry = client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/entries",
        json={"layer": "SOURCE_TEXT", "quran_ref": "1:1", "content": "typed by a user"},
    ).json()
    assert entry["content"] == "PLACEHOLDER-V1-1-1 نص تجريبي", "source text comes from the approved source"
    missing = client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/entries", json={"layer": "SOURCE_TEXT", "quran_ref": "1:99"}
    )
    assert missing.status_code == 404

    unapproved_interpretation = client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/entries",
        json={"layer": "APPROVED_INTERPRETATION", "content": "reading"},
    )
    assert unapproved_interpretation.status_code == 422


def test_not_in_conflict_is_not_support(client: TestClient) -> None:
    pid = _project(client)
    rid = _review(client, pid, _hypothesis(client, pid))
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/entries",
        json={"layer": "PRACTICAL_JUDGMENT", "content": "No conflicting principle identified"},
    )
    supported = client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/judgments",
        json={"state": "REFERENCE_SUPPORTED", "directness": "DIRECT", "rationale": "seems fine"},
    )
    assert supported.status_code == 422
    ok = client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/judgments",
        json={"state": "NOT_IN_CONFLICT", "directness": "EXPLORATORY", "rationale": "no conflict found"},
    )
    assert ok.status_code == 201
    assert ok.json()["state"] == "NOT_IN_CONFLICT"
    assert contract_errors("reference.ReferenceJudgment", as_contract(ok.json(), drop=frozenset({"decision_id"}))) == []


def test_blocking_reservation_raises_blocking_decision_and_blocks_design(client: TestClient, session: Session) -> None:
    pid = _project(client)
    hid = _hypothesis(client, pid)
    rid = _review(client, pid, hid)
    judgment = client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/judgments",
        json={
            "state": "RESERVED",
            "reservation_type": "BLOCKING_RESERVATION",
            "directness": "INFERENTIAL",
            "rationale": "Approved readings differ",
            "divergence": {
                "interpretation_a": "Permitted with conditions",
                "interpretation_b": "Not permitted",
                "implications": "Design must wait",
                "required_authority": "CONSTITUTIONAL_AUTHORITY",
            },
        },
    ).json()
    assert judgment["decision_id"]
    attention = client.get(f"/api/v1/projects/{pid}/attention").json()
    assert attention[0]["level"] == "BLOCKING" and "Blocking reference reservation" in attention[0]["title"]

    standing = client.get(f"/api/v1/projects/{pid}/standing/HYPOTHESIS/{hid}").json()
    assert standing["reference"]["result"] == "BLOCKED"

    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(
            text("UPDATE reference_judgments SET state = 'NOT_IN_CONFLICT' WHERE id = :id"), {"id": judgment["id"]}
        )

    # Human resolves the decision, then records a new judgment; history keeps both.
    client.post(
        f"/api/v1/projects/{pid}/decisions/{judgment['decision_id']}/resolve",
        json={"final_decision": "Lift the reservation", "human_justification": "Authority ruled"},
    )
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/judgments",
        json={"state": "NOT_IN_CONFLICT", "directness": "INFERENTIAL", "rationale": "Authority ruling applied"},
    )
    review = client.get(f"/api/v1/projects/{pid}/reference-reviews/{rid}").json()
    assert [j["state"] for j in review["judgments"]] == ["RESERVED", "NOT_IN_CONFLICT"]
    assert client.get(f"/api/v1/projects/{pid}/standing/HYPOTHESIS/{hid}").json()["reference"]["result"] == "PASS"


def test_missing_review_is_risk_aware(client: TestClient) -> None:
    low, high = _project(client), _project(client, "L3_HIGH_IMPACT")
    assert (
        client.get(f"/api/v1/projects/{low}/standing/HYPOTHESIS/{_hypothesis(client, low)}").json()["reference"][
            "result"
        ]
        == "PASS_WITH_RESERVATIONS"
    )
    assert (
        client.get(f"/api/v1/projects/{high}/standing/HYPOTHESIS/{_hypothesis(client, high)}").json()["reference"][
            "result"
        ]
        == "BLOCKED"
    )


def _make_design_ready(client: TestClient, pid: str, hid: str) -> None:
    """Formulate, add two independent supports, complete counter-evidence tracks, assess SUPPORTED."""
    content = {
        "statement": "h",
        "context": "c",
        "expected_outcome": "o",
        "falsification_conditions": ["f"],
        "proposed_mechanism": "m",
        "assumptions": ["a"],
        "boundary_conditions": ["b"],
    }
    client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/revise", json={"content": content, "change_reason": "formulate"}
    )
    for title in ("Study one", "Study two"):
        work = client.post("/api/v1/sources", json={"work": {"title": title}, "project_id": pid}).json()
        req = client.post(
            f"/api/v1/projects/{pid}/access-requests",
            json={
                "edition_id": work["editions"][0]["id"],
                "reason": "r",
                "requested_scope": "p1",
                "acceptable_forms": ["EXACT_TEXT"],
            },
        ).json()
        ex = client.post(
            f"/api/v1/projects/{pid}/access-requests/{req['id']}/responses",
            json={"form": "EXACT_TEXT", "location": "p1", "text": title},
        ).json()["excerpt"]["id"]
        ev = client.post(
            f"/api/v1/projects/{pid}/evidence",
            json={
                "target_type": "HYPOTHESIS",
                "target_id": hid,
                "role": "SUPPORTS",
                "finding": "effective",
                "excerpt_id": ex,
            },
        ).json()
        client.post(
            f"/api/v1/projects/{pid}/evidence/{ev['id']}/assess", json={"decision": "ACCEPT", "strength": "STRONG"}
        )
    for track in ("CHALLENGE", "ALTERNATIVE_EXPLANATION"):
        client.post(
            f"/api/v1/projects/{pid}/research-tracks",
            json={
                "target_type": "HYPOTHESIS",
                "target_id": hid,
                "track": track,
                "outcome": "NO_RELEVANT_EVIDENCE_FOUND",
                "scope": "local library",
            },
        )
    client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/assess", json={"epistemic_state": "SUPPORTED", "reason": "2 origins"}
    )
    for step in ("FORMULATED_HYPOTHESIS", "UNDER_REFERENCE_REVIEW", "UNDER_SCRUTINY", "UNDER_RESEARCH", "ASSESSED"):
        assert (
            client.post(
                f"/api/v1/projects/{pid}/hypotheses/{hid}/transition", json={"target": step, "reason": "progress"}
            ).status_code
            == 200
        )


def test_scenario_e_effective_but_reference_rejected(client: TestClient) -> None:
    pid = _project(client)
    hid = _hypothesis(client, pid)
    mechanism = client.post(
        f"/api/v1/projects/{pid}/mechanisms", json={"name": "Peer accountability", "description": "Reusable mechanism"}
    ).json()
    client.post(f"/api/v1/projects/{pid}/hypotheses/{hid}/mechanisms", json={"mechanism_id": mechanism["id"]})
    _make_design_ready(client, pid, hid)
    rid = _review(client, pid, hid)
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/judgments",
        json={"state": "REJECTED", "directness": "CLOSE", "rationale": "Means conflict with a binding limit"},
    )

    blocked = client.post(
        f"/api/v1/projects/{pid}/hypotheses/{hid}/transition",
        json={"target": "ELIGIBLE_FOR_DESIGN", "reason": "effective"},
    )
    assert blocked.status_code == 422
    codes = {f["code"] for f in blocked.json()["error"]["details"]["findings"]}
    assert codes == {"reference.not_cleared"}, "effectiveness does not override the reference rejection"
    hypothesis = client.get(f"/api/v1/projects/{pid}/hypotheses/{hid}").json()
    assert hypothesis["epistemic_state"] == "SUPPORTED", "empirical support is still recorded honestly"
    assert hypothesis["mechanism_ids"] == [mechanism["id"]], "useful mechanisms are preserved for other designs"


def test_scenario_f_legal_constraint_does_not_change_reference_judgment(
    client: TestClient, approved_quran: dict[str, Any]
) -> None:
    pid = _project(client)
    hid = _hypothesis(client, pid)
    rid = _review(client, pid, hid)
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/entries", json={"layer": "SOURCE_TEXT", "quran_ref": "1:2"}
    )
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{rid}/judgments",
        json={
            "state": "REFERENCE_CONSISTENT",
            "directness": "INFERENTIAL",
            "rationale": "Consistent with the cited principle",
        },
    )
    constraint = client.post(
        f"/api/v1/projects/{pid}/operational-constraints",
        json={
            "target_type": "HYPOTHESIS",
            "target_id": hid,
            "kind": "REGULATION",
            "state": "BLOCKS_CURRENT_EXECUTION",
            "description": "Current licensing rules forbid this pilot",
            "jurisdiction": "Region X",
            "required_change": "Apply for a regulatory sandbox",
        },
    ).json()
    contract = {k: v for k, v in as_contract(constraint).items() if k not in {"resolved_at", "resolution"}}
    assert contract_errors("reference.OperationalConstraint", {**contract, "resolved": False}) == []

    standing = client.get(f"/api/v1/projects/{pid}/standing/HYPOTHESIS/{hid}").json()
    assert standing["reference"]["result"] == "PASS"
    assert standing["reference"]["latest_judgments"][0]["state"] == "REFERENCE_CONSISTENT"
    assert standing["operational"]["execution_ready"] is False
    assert standing["operational"]["researchable"] is True
    assert "prevent execution now" in standing["summary"]

    client.post(
        f"/api/v1/projects/{pid}/operational-constraints/{constraint['id']}/resolve",
        json={"resolution": "Sandbox approved"},
    )
    assert (
        client.get(f"/api/v1/projects/{pid}/standing/HYPOTHESIS/{hid}").json()["operational"]["execution_ready"] is True
    )
