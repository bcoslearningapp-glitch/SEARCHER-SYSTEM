"""Research Orchestrator: AI tasks become validated proposals through domain services (issue #22).

Every test uses the deterministic mock provider; no network calls are made.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.modules.ai_gateway import mock_adapter
from research_api.modules.ai_gateway import profiles as registry
from research_api.modules.ai_gateway.base import ProviderOutputError, ProviderUnavailableError, StructuredRequest
from research_api.modules.research_orchestrator import service as orchestrator
from research_api.modules.sources_library import ingestion
from research_api.platform import jobs, queue
from research_api.platform.errors import RuleViolationError
from tests.pdf_fixtures import make_pdf

FRAME = {
    "central_issue": "Second-year apprentices disengage",
    "current_state": "Engagement falls in year two",
    "desired_state": "Engagement holds through year three",
    "gap": "Unknown drivers of the drop",
    "current_explanations": ["Mentoring ends after year one", " "],
    "initial_hypotheses": ["Mentoring loss drives disengagement"],
    "context": "Regional apprenticeship programme",
    "constraints": [],
    "known": ["Drop starts in month 13"],
    "unknowns": ["Role of wages"],
    "research_questions": ["What changes at month 13?"],
    "reference_review_points": [],
}
CONTRA = "Retention rose where mentoring was cut in 2021."
WAGES = "Wage cuts preceded disengagement in every cohort studied."


@pytest.fixture(autouse=True)
def _mock_ai(monkeypatch: MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AI_MOCK_ENABLED", "true")
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)
    get_settings.cache_clear()
    registry.reset_cache()
    yield
    mock_adapter.STATE.mode = "ok"
    mock_adapter.STATE.responders.clear()
    get_settings.cache_clear()
    registry.reset_cache()


def _project(client: TestClient) -> str:
    body = {"title": "Apprentices", "initial_input": "Why do apprentices disengage?", "input_type": "RAW_QUESTION"}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _launch(client: TestClient, pid: str, **body: Any) -> str:
    response = client.post(f"/api/v1/projects/{pid}/ai-tasks", json={"profile": "mock", **body})
    assert response.status_code == 202, response.text
    assert response.json()["state"] == "QUEUED"
    return str(response.json()["id"])


def _run(session: Session, job_id: str) -> dict[str, Any]:
    return orchestrator.run(session, jobs.get_job(session, UUID(job_id)))


def test_draft_problem_frame_lands_as_ai_draft_with_provenance(client: TestClient, session: Session) -> None:
    mock_adapter.register("draft_problem_frame", lambda _r: FRAME)
    pid = _project(client)
    result = _run(session, _launch(client, pid, task="draft_problem_frame"))
    assert result["status"] == "DRAFT"
    [frame] = client.get(f"/api/v1/projects/{pid}/problem-frames").json()
    assert frame["status"] == "DRAFT"
    assert frame["content"]["current_explanations"] == ["Mentoring ends after year one"]
    assert frame["provenance"]["kind"] == "AI_GENERATED"
    assert frame["provenance"]["ai_action"]["template_version"] == "draft_problem_frame@1"
    assert frame["provenance"]["ai_action"]["provider"] == "mock"
    assert client.get(f"/api/v1/projects/{pid}").json()["status"] == "FRAMING"


def test_ai_never_overwrites_a_researchers_draft(client: TestClient, session: Session) -> None:
    mock_adapter.register("draft_problem_frame", lambda _r: FRAME)
    pid = _project(client)
    human = client.put(f"/api/v1/projects/{pid}/problem-frames/draft", json={"content": {"central_issue": "Mine"}})
    assert human.status_code == 200, human.text
    job_id = _launch(client, pid, task="draft_problem_frame")
    with pytest.raises(RuleViolationError):
        _run(session, job_id)
    [frame] = client.get(f"/api/v1/projects/{pid}/problem-frames").json()
    assert frame["content"]["central_issue"] == "Mine"


def test_detected_assumptions_are_unconfirmed_and_deduplicated(client: TestClient, session: Session) -> None:
    pid = _project(client)
    client.post(f"/api/v1/projects/{pid}/assumptions", json={"statement": "Mentors are available"})
    mock_adapter.register(
        "detect_assumptions",
        lambda _r: {
            "assumptions": [
                {"statement": "Mentors are available.", "criticality": "HIGH", "rationale": "dup of existing"},
                {"statement": "Engagement surveys are comparable", "criticality": "FOUNDATIONAL", "rationale": "r"},
                {"statement": "engagement surveys are comparable", "criticality": "LOW", "rationale": "dup"},
            ]
        },
    )
    result = _run(session, _launch(client, pid, task="detect_assumptions"))
    assert len(result["assumption_ids"]) == 1
    ai = [a for a in client.get(f"/api/v1/projects/{pid}/assumptions").json() if a["id"] in result["assumption_ids"]]
    assert ai[0]["status"] == "UNCONFIRMED"
    assert ai[0]["origin"] == "SYSTEM_INFERRED"
    assert ai[0]["criticality"] == "FOUNDATIONAL"


def test_invalid_output_is_retried_once_then_surfaced_without_mutation(client: TestClient, session: Session) -> None:
    pid = _project(client)
    mock_adapter.register("detect_assumptions", lambda _r: {"assumptions": [{"statement": "x"}]})
    job_id = _launch(client, pid, task="detect_assumptions")
    with pytest.raises(ProviderOutputError):
        _run(session, job_id)
    assert client.get(f"/api/v1/projects/{pid}/assumptions").json() == []
    log = client.get(f"/api/v1/projects/{pid}/ai-requests").json()
    assert [e["error_kind"] for e in log] == ["INVALID_STRUCTURED_OUTPUT"] * 2


def test_retry_recovers_from_one_invalid_output(client: TestClient, session: Session) -> None:
    pid = _project(client)
    calls = {"n": 0}

    def flaky(_r: StructuredRequest) -> dict[str, Any]:
        calls["n"] += 1
        if calls["n"] == 1:
            return {"assumptions": "not a list"}
        return {"assumptions": [{"statement": "Cohorts are comparable", "criticality": "MEDIUM", "rationale": "r"}]}

    mock_adapter.register("detect_assumptions", flaky)
    assert len(_run(session, _launch(client, pid, task="detect_assumptions"))["assumption_ids"]) == 1


def _hypothesis_with_library(client: TestClient, session: Session, pid: str) -> str:
    hypothesis = client.post(
        f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "Mentoring loss drives disengagement"}}
    ).json()
    work = client.post("/api/v1/sources", json={"work": {"title": "Cohort study"}, "project_id": pid}).json()
    asset = client.post(
        f"/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
        files={"file": ("c.pdf", make_pdf([CONTRA, WAGES]), "application/pdf")},
    ).json()
    ingestion.ingest_asset(session, UUID(asset["id"]))
    return str(hypothesis["id"])


def _assess(request: StructuredRequest) -> dict[str, Any]:
    candidates = []
    for section in request.sections:
        if section.kind != "retrieved_source":
            continue
        if "Retention" in section.content:
            candidates.append(
                {"passage_id": section.source_id, "role": "CONTRADICTS", "alternative_index": -1, "finding": "Counter"}
            )
        if "Wage" in section.content:
            candidates.append(
                {"passage_id": section.source_id, "role": "QUALIFIES", "alternative_index": 0, "finding": "Wages"}
            )
    candidates.append({"passage_id": "P99", "role": "SUPPORTS", "alternative_index": -1, "finding": "invented"})
    return {"candidates": candidates, "alternative_support": [{"alternative_index": 0, "strength": "STRONG"}]}


def test_challenge_this_proposes_candidates_tracks_and_competing_hypotheses(
    client: TestClient, session: Session
) -> None:
    pid = _project(client)
    hid = _hypothesis_with_library(client, session, pid)
    mock_adapter.register(
        "plan_challenge",
        lambda _r: {
            "challenge_queries": ["retention mentoring cut"],
            "alternative_explanations": [{"statement": "Wage cuts drive disengagement", "queries": ["wage cuts"]}],
        },
    )
    mock_adapter.register("assess_passages", _assess)
    result = _run(session, _launch(client, pid, task="challenge", target_type="HYPOTHESIS", target_id=hid))

    assert len(result["evidence_candidate_ids"]) == 2, "a passage the model was not given is ignored"
    evidence_map = client.get(f"/api/v1/projects/{pid}/evidence-map/HYPOTHESIS/{hid}").json()
    assert {c["status"] for c in evidence_map["candidates"]} == {"CANDIDATE"}
    assert {c["track"] for c in evidence_map["candidates"]} == {"CHALLENGE", "ALTERNATIVE_EXPLANATION"}
    for candidate in evidence_map["candidates"]:
        excerpt = client.get(f"/api/v1/sources/excerpts/{candidate['excerpt_id']}").json()
        assert excerpt["text"] in (CONTRA, WAGES), "quotes are copied from the page, never from the model"
        assert excerpt["is_exact_quote"] is True
    tracks = {t["track"]: t for t in evidence_map["tracks"]}
    assert tracks["CHALLENGE"]["last_outcome"] == "RESULTS_FOUND"
    assert tracks["ALTERNATIVE_EXPLANATION"]["last_outcome"] == "RESULTS_FOUND"
    assert evidence_map["counter_evidence_search_complete"] is True

    [competitor_id] = result["competing_hypothesis_ids"]
    competitor = client.get(f"/api/v1/projects/{pid}/hypotheses/{competitor_id}").json()
    assert competitor["lifecycle_state"] == "SIGNAL"
    assert competitor["provenance"]["kind"] == "AI_GENERATED"
    target = client.get(f"/api/v1/projects/{pid}/hypotheses/{hid}").json()
    assert competitor_id in target["competing_hypothesis_ids"]
    assert target["epistemic_state"] == "UNRESOLVED", "candidates change nothing until a human accepts them"


def test_challenge_with_empty_library_reports_insufficient_coverage(client: TestClient, session: Session) -> None:
    pid = _project(client)
    claim = client.post(
        f"/api/v1/projects/{pid}/claims", json={"statement": "Mentors matter", "claim_type": "FACTUAL_CLAIM"}
    ).json()
    mock_adapter.register(
        "plan_challenge", lambda _r: {"challenge_queries": ["mentors"], "alternative_explanations": []}
    )
    _run(session, _launch(client, pid, task="challenge", target_type="CLAIM", target_id=claim["id"]))
    evidence_map = client.get(f"/api/v1/projects/{pid}/evidence-map/CLAIM/{claim['id']}").json()
    outcomes = {t["track"]: t["last_outcome"] for t in evidence_map["tracks"]}
    assert outcomes["CHALLENGE"] == "INSUFFICIENT_SEARCH_COVERAGE"
    assert evidence_map["counter_evidence_search_complete"] is False


def test_provider_outage_is_recorded_as_execution_failure_not_absence(client: TestClient, session: Session) -> None:
    pid = _project(client)
    hid = _hypothesis_with_library(client, session, pid)
    mock_adapter.STATE.mode = "unavailable"
    job_id = _launch(client, pid, task="challenge", target_type="HYPOTHESIS", target_id=hid)
    with pytest.raises(ProviderUnavailableError):
        _run(session, job_id)
    job = jobs.get_job(session, UUID(job_id))
    job.failure_kind = jobs.JobFailureKind.PROVIDER_ERROR.value  # as the worker runner records it
    orchestrator.on_failure(session, job)
    evidence_map = client.get(f"/api/v1/projects/{pid}/evidence-map/HYPOTHESIS/{hid}").json()
    tracks = {t["track"]: t for t in evidence_map["tracks"]}
    assert tracks["CHALLENGE"]["execution_failed"] is True
    assert tracks["CHALLENGE"]["searched"] is False
    assert evidence_map["counter_evidence_search_complete"] is False
    assert evidence_map["candidates"] == []
    # The project stays fully usable without the provider.
    assert client.get(f"/api/v1/projects/{pid}/hypotheses/{hid}").status_code == 200


def test_cancelled_task_writes_nothing(client: TestClient, session: Session) -> None:
    mock_adapter.register("draft_problem_frame", lambda _r: FRAME)
    pid = _project(client)
    job = jobs.get_job(session, UUID(_launch(client, pid, task="draft_problem_frame")))
    job.cancel_requested = True
    session.flush()
    with pytest.raises(jobs.JobCancelledError), session.begin_nested():
        orchestrator.run(session, job)
    assert client.get(f"/api/v1/projects/{pid}/problem-frames").json() == []


def test_launch_validation_and_task_list(client: TestClient) -> None:
    pid = _project(client)
    missing = client.post(f"/api/v1/projects/{pid}/ai-tasks", json={"task": "challenge"})
    assert missing.status_code == 422
    unknown = client.post(
        f"/api/v1/projects/{pid}/ai-tasks",
        json={"task": "challenge", "target_type": "HYPOTHESIS", "target_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert unknown.status_code == 404
    job_id = _launch(client, pid, task="detect_assumptions")
    listed = client.get(f"/api/v1/projects/{pid}/ai-tasks").json()
    assert [j["id"] for j in listed] == [job_id]
    assert listed[0]["kind"] == "orchestrator.detect_assumptions"
