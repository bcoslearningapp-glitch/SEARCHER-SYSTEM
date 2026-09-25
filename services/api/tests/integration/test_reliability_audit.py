"""Installation audit of the blocking evaluation dimensions (#56, QUALITY_GATES)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session

from research_api.modules.ai_reliability import audit
from research_api.modules.ai_tools.models import AIToolCall
from research_api.modules.governance_audit.policy import PolicyViolationError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.outputs_integrity.models import OutputVersion
from research_api.platform import jobs, queue
from tests.integration.test_outputs import PASSAGE, _create, _project_with_evidence
from tests.integration.test_reference import approved_quran  # noqa: F401 - fixture

AUDIT = "/api/v1/ai/reliability/audit"


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


def _audit(client: TestClient) -> dict[str, dict[str, Any]]:
    response = client.post(AUDIT)
    assert response.status_code == 201, response.text
    return {row["dimension"]: row for row in response.json()}


def _tampered_version(session: Session, output: dict[str, Any]) -> None:
    """A version whose quote no longer matches its source, as a bug or a manual database edit would leave it."""
    blocks = [dict(b) for b in output["latest"]["blocks"]]
    for block in blocks:
        if block["kind"] == "QUOTE":
            block["quote"] = {**block["quote"], "text": PASSAGE + " (altered)"}
            block["text"] = PASSAGE + " (altered)"
    session.add(
        OutputVersion(
            output_id=UUID(output["id"]), version_number=99, status="DRAFT", blocks=blocks, created_by={"kind": "HUMAN"}
        )
    )
    session.flush()


def test_a_clean_installation_passes_every_audited_dimension(client: TestClient) -> None:
    pid, _, _ = _project_with_evidence(client)
    _create(client, pid)
    rows = _audit(client)
    assert set(rows) == {
        "exact_quote_fidelity",
        "quran_hadith_integrity",
        "claim_source_separation",
        "tool_use_correctness",
    }
    assert rows["exact_quote_fidelity"]["score"] == 1.0 and rows["exact_quote_fidelity"]["sample_size"] >= 1
    assert all(r["method"] == "AUTOMATED_AUDIT" and r["provider"] == "installation" for r in rows.values())
    assert rows["exact_quote_fidelity"]["passed"] and rows["claim_source_separation"]["passed"]
    standing = next(m for m in client.get("/api/v1/ai/reliability").json()["models"] if m["provider"] == "installation")
    assert standing["blocking_unevaluated"] == [], "the installation row lists only the audited dimensions"


def test_an_altered_quote_fails_exact_quote_fidelity(client: TestClient, session: Session) -> None:
    pid, _, _ = _project_with_evidence(client)
    output = _create(client, pid)
    _tampered_version(session, output)
    row = _audit(client)["exact_quote_fidelity"]
    assert row["passed"] is False and row["score"] < 1.0
    assert any(f["output_version"] for f in row["details"]["failures"])


def test_a_tool_run_outside_its_task_allow_list_is_counted(client: TestClient, session: Session) -> None:
    pid, _, _ = _project_with_evidence(client)
    before = _audit(client)["tool_use_correctness"]["details"]["violations"]
    job = jobs.create_job(session, "ai_task", params={"task": "detect_assumptions"}, project_id=UUID(pid))
    session.add(
        AIToolCall(
            project_id=UUID(pid),
            job_id=job.id,
            tool="propose_evidence",  # a real tool, but not allowed for detect_assumptions
            kind="PROPOSE",
            status="OK",
            arguments={},
            output_ids=[],
            principal_id="research_orchestrator",
        )
    )
    session.flush()
    row = _audit(client)["tool_use_correctness"]
    assert row["details"]["violations"] == before + 1
    assert row["passed"] is False


def test_an_ai_principal_cannot_run_the_audit(session: Session) -> None:
    with pytest.raises(PolicyViolationError):
        audit.run(session, ai_principal("research_orchestrator"))


def test_a_quran_quote_not_matching_the_approved_text_is_counted(
    client: TestClient,
    session: Session,
    approved_quran: dict[str, Any],  # noqa: F811
) -> None:
    pid = str(
        client.post("/api/v1/projects", json={"title": "Q", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    )
    hid = client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "h"}}).json()["id"]
    review = client.post(
        f"/api/v1/projects/{pid}/reference-reviews",
        json={
            "target_type": "HYPOTHESIS",
            "target_id": hid,
            "question": "Q?",
            "analytical_category": "VALUES_AND_EVALUATIVE_STANDARDS",
        },
    ).json()
    client.post(
        f"/api/v1/projects/{pid}/reference-reviews/{review['id']}/entries",
        json={"layer": "SOURCE_TEXT", "quran_ref": "1:2"},
    )
    output = _create(client, pid, output_type="REFERENCE_REVIEW", language="ar")
    clean = _audit(client)["quran_hadith_integrity"]
    assert clean["passed"] and clean["details"]["checked"] >= 1
    _tampered_version(session, output)
    tampered = _audit(client)["quran_hadith_integrity"]
    assert tampered["score"] == clean["score"] + 1 and tampered["passed"] is False
