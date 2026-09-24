"""Research plans, search audit, web results as leads, and sufficiency (issue #25). Mocked providers only."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.schemas import contract_errors
from research_api.modules.ai_gateway import mock_adapter
from research_api.modules.ai_gateway import profiles as registry
from research_api.modules.ai_gateway.base import ProviderUnavailableError, WebResult
from research_api.modules.ai_gateway.service import DisclosureBlockedError, ResourceConstraintError
from research_api.modules.research_orchestrator import service as orchestrator
from research_api.modules.sources_library import ingestion
from research_api.platform import jobs, queue
from tests.contract_helpers import as_contract
from tests.pdf_fixtures import make_pdf

CONSIDERATIONS = {
    k: "Recorded."
    for k in (
        "support_evidence",
        "counter_evidence",
        "alternative_explanations",
        "independence",
        "diversity",
        "context_fit",
        "critical_unknowns",
        "impact",
        "reversibility",
        "remaining_uncertainty",
    )
}


@pytest.fixture(autouse=True)
def _mock_ai(monkeypatch: MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AI_MOCK_ENABLED", "true")
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)
    get_settings.cache_clear()
    registry.reset_cache()
    yield
    mock_adapter.STATE.mode = "ok"
    mock_adapter.STATE.web_results.clear()
    get_settings.cache_clear()
    registry.reset_cache()


def _project(client: TestClient, sensitivity: str = "NORMAL") -> str:
    body = {"title": "Plans", "initial_input": "Q", "input_type": "RAW_QUESTION", "sensitivity": sensitivity}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _plan_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "question": "What drives year-two disengagement?",
        "decision_served": "Whether to fund second-year mentoring",
        "question_type": "EMPIRICAL",
        "languages": ["en", "fr"],
        "tracks": [
            {"track": "SUPPORT", "approach": "Mentoring and retention studies", "queries": ["mentoring retention"]},
            {"track": "CHALLENGE", "approach": "Cases where losing mentors changed nothing"},
            {"track": "ALTERNATIVE_EXPLANATION", "approach": "Pay and workload"},
        ],
        "sufficiency_criteria": ["Two independent origins on the main driver"],
    }
    return body | overrides


def _plan(client: TestClient, pid: str, **overrides: Any) -> dict[str, Any]:
    response = client.post(f"/api/v1/projects/{pid}/research-plans", json=_plan_body(**overrides))
    assert response.status_code == 201, response.text
    return dict(response.json())


def test_plan_must_cover_all_tracks_and_is_versioned(client: TestClient, session: Session) -> None:
    pid = _project(client)
    two_tracks = _plan_body(tracks=_plan_body()["tracks"][:2])
    assert client.post(f"/api/v1/projects/{pid}/research-plans", json=two_tracks).status_code == 422
    bad_language = _plan_body(languages=["English"])
    assert client.post(f"/api/v1/projects/{pid}/research-plans", json=bad_language).status_code == 422

    v1 = _plan(client, pid)
    assert (
        contract_errors(
            "research.ResearchPlan",
            as_contract(v1, drop=frozenset({"series_id", "status", "change_reason", "created_at"})),
        )
        == []
    )
    revised = client.post(
        f"/api/v1/projects/{pid}/research-plans/{v1['id']}/revise",
        json=_plan_body(question="What drives year-two and year-three disengagement?", change_reason="Scope widened"),
    )
    assert revised.status_code == 201, revised.text
    v2 = revised.json()
    assert v2["version_number"] == 2 and v2["supersedes_id"] == v1["id"]
    assert [p["id"] for p in client.get(f"/api/v1/projects/{pid}/research-plans").json()] == [v2["id"]]
    again = client.post(
        f"/api/v1/projects/{pid}/research-plans/{v1['id']}/revise", json=_plan_body(change_reason="stale")
    )
    assert again.status_code == 409

    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(text("UPDATE research_plans SET question = 'rewritten' WHERE id = :i"), {"i": v1["id"]})
    with pytest.raises(DBAPIError, match="cannot be deleted"), session.begin_nested():
        session.execute(text("DELETE FROM research_plans WHERE id = :i"), {"i": v2["id"]})


def _library(client: TestClient, session: Session, pid: str) -> None:
    work = client.post("/api/v1/sources", json={"work": {"title": "Cohort study"}, "project_id": pid}).json()
    asset = client.post(
        f"/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
        files={"file": ("c.pdf", make_pdf(["Mentoring loss preceded disengagement."]), "application/pdf")},
    ).json()
    ingestion.ingest_asset(session, UUID(asset["id"]))


def _local(client: TestClient, pid: str, plan_id: str, track: str, query: str) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{pid}/searches/local",
        json={"plan_id": plan_id, "track": track, "queries": [query], "languages": ["en"]},
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def test_local_search_is_audited_with_bounded_outcomes(client: TestClient, session: Session) -> None:
    pid = _project(client)
    plan = _plan(client, pid)
    empty = _local(client, pid, plan["id"], "SUPPORT", "mentoring")
    assert empty["records"][0]["outcome"] == "INSUFFICIENT_SEARCH_COVERAGE", "nothing ingested is not 'no evidence'"

    _library(client, session, pid)
    found = _local(client, pid, plan["id"], "SUPPORT", "mentoring")
    assert found["records"][0]["outcome"] == "RESULTS_FOUND"
    assert found["hits"] and found["hits"][0]["work_title"] == "Cohort study"
    none = _local(client, pid, plan["id"], "CHALLENGE", "zeppelin")
    record = none["records"][0]
    assert record["outcome"] == "NO_RELEVANT_EVIDENCE_FOUND"
    assert record["provider"] == "local_library" and record["question"] == plan["question"]
    assert contract_errors("research.SearchRecord", as_contract(record, drop=frozenset())) == []

    overview = client.get(f"/api/v1/projects/{pid}/research-plans/{plan['id']}").json()
    coverage = {c["track"]: c for c in overview["coverage"]}
    assert coverage["SUPPORT"]["searches"] == 2 and coverage["SUPPORT"]["searched"] is True
    assert coverage["CHALLENGE"]["searched"] is True
    assert coverage["ALTERNATIVE_EXPLANATION"]["searched"] is False

    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("UPDATE search_records SET outcome = 'RESULTS_FOUND' WHERE project_id = :p"), {"p": pid})


def _web_job(client: TestClient, pid: str, **body: Any) -> str:
    response = client.post(f"/api/v1/projects/{pid}/ai-tasks", json={"task": "web_search", "profile": "mock", **body})
    assert response.status_code == 202, response.text
    return str(response.json()["id"])


def _run(session: Session, job_id: str) -> dict[str, Any]:
    return orchestrator.run(session, jobs.get_job(session, UUID(job_id)))


def _fail(session: Session, job_id: str, kind: jobs.JobFailureKind, error: str) -> None:
    job = jobs.get_job(session, UUID(job_id))
    job.failure_kind, job.error = kind.value, error  # as the worker runner records it
    orchestrator.on_failure(session, job)


def test_web_results_become_leads_not_evidence(client: TestClient, session: Session) -> None:
    pid = _project(client)
    plan = _plan(client, pid)
    mock_adapter.STATE.web_results["mentoring retention"] = [
        WebResult("https://example.org/review", "Retention review", "mentoring retention"),
        WebResult("https://example.org/review", "Retention review (dup)", "mentoring retention"),
        WebResult("https://example.org/pay", "Pay progression study", "mentoring retention"),
    ]
    body = {"plan_id": plan["id"], "track": "SUPPORT", "queries": ["mentoring retention"], "languages": ["en"]}
    result = _run(session, _web_job(client, pid, **body))
    assert result["outcome"] == "RESULTS_FOUND" and result["results"] == 2
    leads = [
        lead for lead in client.get(f"/api/v1/projects/{pid}/source-leads").json() if lead["origin"] == "WEB_SEARCH"
    ]
    assert {lead["url"] for lead in leads} == {"https://example.org/review", "https://example.org/pay"}
    assert {lead["status"] for lead in leads} == {"SOURCE_LEAD"}
    assert contract_errors("source-identity.SourceLead", as_contract(leads[0], drop=frozenset({"created_at"}))) == []

    again = _run(session, _web_job(client, pid, **body))
    assert again["lead_ids"] == [], "a URL already held as a lead is not duplicated"

    overview = client.get(f"/api/v1/projects/{pid}/research-plans/{plan['id']}").json()
    assert overview["web_searches_used"] == 2
    web = [s for s in overview["searches"] if s["provider"] == "web"]
    assert web[0]["actor"]["kind"] == "AI"
    log = client.get(f"/api/v1/projects/{pid}/ai-requests").json()
    assert {e["task"] for e in log} == {"web_search"}
    assert all(e["status"] == "SUCCEEDED" for e in log)


def test_web_search_budget_trims_then_stops(client: TestClient, session: Session) -> None:
    pid = _project(client)
    plan = _plan(client, pid, max_web_searches=1)
    body = {"plan_id": plan["id"], "track": "CHALLENGE", "queries": ["q one", "q two"]}
    first = _run(session, _web_job(client, pid, **body))
    assert first["outcome"] == "NO_RELEVANT_EVIDENCE_FOUND"
    assert mock_adapter.STATE.web_calls[-1].queries == ["q one"], "trimmed to the remaining budget"

    job_id = _web_job(client, pid, **body)
    with pytest.raises(ResourceConstraintError):
        _run(session, job_id)
    _fail(session, job_id, jobs.JobFailureKind.STOPPED_RESOURCE_CONSTRAINT, "budget used up")
    overview = client.get(f"/api/v1/projects/{pid}/research-plans/{plan['id']}").json()
    assert overview["searches"][0]["outcome"] == "STOPPED_RESOURCE_CONSTRAINT"


def test_web_outage_and_disclosure_are_not_absence(client: TestClient, session: Session) -> None:
    pid = _project(client)
    plan = _plan(client, pid)
    mock_adapter.STATE.mode = "unavailable"
    job_id = _web_job(client, pid, plan_id=plan["id"], track="CHALLENGE", queries=["mentoring cut"])
    with pytest.raises(ProviderUnavailableError):
        _run(session, job_id)
    _fail(session, job_id, jobs.JobFailureKind.PROVIDER_ERROR, "mock outage")
    overview = client.get(f"/api/v1/projects/{pid}/research-plans/{plan['id']}").json()
    challenge = next(c for c in overview["coverage"] if c["track"] == "CHALLENGE")
    assert challenge["execution_failed"] is True and challenge["searched"] is False

    restricted = _project(client, "RESTRICTED")
    job_id = _web_job(client, restricted, question="Anything", queries=["x"], profile="anthropic-default")
    with pytest.raises(DisclosureBlockedError):
        _run(session, job_id)
    assert client.get(f"/api/v1/projects/{restricted}/ai-requests").json()[0]["status"] == "BLOCKED"


def test_sufficiency_is_human_decision_relative_and_needs_counter_search(client: TestClient, session: Session) -> None:
    pid = _project(client)
    plan = _plan(client, pid)
    url = f"/api/v1/projects/{pid}/research-plans/{plan['id']}/sufficiency"
    body = {"result": "SUFFICIENTLY_ANSWERED", "considerations": CONSIDERATIONS, "rationale": "Enough."}
    blocked = client.post(url, json=body)
    assert blocked.status_code == 422
    assert set(blocked.json()["error"]["details"]["unsearched_tracks"]) == {"CHALLENGE", "ALTERNATIVE_EXPLANATION"}
    partial = {**CONSIDERATIONS}
    del partial["reversibility"]
    assert client.post(url, json={**body, "considerations": partial}).status_code == 422

    not_known = client.post(
        url,
        json={**body, "result": "INSUFFICIENT_EVIDENCE", "rationale": "Not known yet.", "recommend_experiment": True},
    )
    assert not_known.status_code == 201, not_known.text
    assert (
        contract_errors("research.SufficiencyAssessment", as_contract(not_known.json(), drop=frozenset({"signals"})))
        == []
    )
    assert not_known.json()["decision_served"] == plan["decision_served"]

    _library(client, session, pid)
    _local(client, pid, plan["id"], "CHALLENGE", "zeppelin")
    _local(client, pid, plan["id"], "ALTERNATIVE_EXPLANATION", "wages")
    answered = client.post(url, json=body)
    assert answered.status_code == 201, answered.text
    assert len(answered.json()["signals"]["search_record_ids"]) == 2
    overview = client.get(f"/api/v1/projects/{pid}/research-plans/{plan['id']}").json()
    assert overview["current_sufficiency"]["result"] == "SUFFICIENTLY_ANSWERED"
    assert [s["result"] for s in overview["sufficiency_history"]] == ["SUFFICIENTLY_ANSWERED", "INSUFFICIENT_EVIDENCE"]
    assert contract_errors(
        "research.SufficiencyAssessment", {**not_known.json(), "assessed_by": {"kind": "AI", "id": "x"}}
    )

    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("DELETE FROM sufficiency_assessments WHERE project_id = :p"), {"p": pid})
