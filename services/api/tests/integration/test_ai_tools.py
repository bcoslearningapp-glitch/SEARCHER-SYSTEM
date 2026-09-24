"""Controlled AI tools: server-side scoping, allow-lists, validation and audit (issue #29)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.enums import SensitivityLevel
from research_api.modules.ai_gateway import mock_adapter
from research_api.modules.ai_gateway import profiles as registry_profiles
from research_api.modules.ai_tools import registry
from research_api.modules.ai_tools import tools as _tools  # noqa: F401 - registers the tools
from research_api.modules.ai_tools.registry import ToolContext, ToolDeniedError, ToolInputError
from research_api.modules.governance_audit.principal import ai_principal
from research_api.modules.governance_audit.schemas import AIActionRecord
from research_api.modules.research_orchestrator import service as orchestrator
from research_api.modules.sources_library import ingestion
from research_api.platform import jobs, queue
from research_api.platform.errors import NotFoundError
from tests.pdf_fixtures import make_pdf

AI = ai_principal("research_orchestrator")


@pytest.fixture(autouse=True)
def _mock_ai(monkeypatch: MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AI_MOCK_ENABLED", "true")
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)
    get_settings.cache_clear()
    registry_profiles.reset_cache()
    yield
    mock_adapter.STATE.responders.clear()
    get_settings.cache_clear()
    registry_profiles.reset_cache()


def _project(client: TestClient) -> str:
    body = {"title": "Tools", "initial_input": "Why?", "input_type": "RAW_QUESTION"}
    return str(client.post("/api/v1/projects", json=body).json()["id"])


def _library(client: TestClient, session: Session, pid: str, passage: str) -> None:
    work = client.post("/api/v1/sources", json={"work": {"title": f"Study {pid[:4]}"}, "project_id": pid}).json()
    asset = client.post(
        f"/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
        files={"file": ("s.pdf", make_pdf([passage]), "application/pdf")},
    ).json()
    ingestion.ingest_asset(session, UUID(asset["id"]))


def _ctx(pid: str, *allowed: str, action: bool = False) -> ToolContext:
    ai_action = (
        AIActionRecord(
            provider="mock", model="mock-1", template_version="t@1", task_id=str(uuid4()), timestamp=datetime.now(UTC)
        )
        if action
        else None
    )
    return ToolContext(
        project_id=UUID(pid),
        sensitivity=SensitivityLevel.NORMAL,
        principal=AI,
        requested_by="local-owner",
        allowed=frozenset(allowed),
        ai_action=ai_action,
    )


def _calls(client: TestClient, pid: str) -> list[dict[str, Any]]:
    return list(client.get(f"/api/v1/projects/{pid}/ai-tool-calls").json())


def test_definitions_are_closed_and_never_take_a_project(client: TestClient) -> None:
    tools = client.get("/api/v1/ai/tools").json()
    assert {"search_sources", "propose_evidence", "search_external_web", "get_quran_ayah"} <= {t["name"] for t in tools}
    for tool in tools:
        assert tool["input_schema"]["additionalProperties"] is False
        assert "project_id" not in tool["input_schema"]["properties"]


def test_unknown_and_unlisted_tools_are_refused_and_logged(client: TestClient, session: Session) -> None:
    pid = _project(client)
    ctx = _ctx(pid, "search_sources", action=True)
    with pytest.raises(ToolDeniedError, match="unknown tool"):
        registry.invoke(session, ctx, "drop_all_tables", {})
    with pytest.raises(ToolDeniedError, match="not allowed"):
        registry.invoke(session, ctx, "propose_claim", {"statement": "x", "claim_type": "FACTUAL_CLAIM"})
    assert client.get(f"/api/v1/projects/{pid}/claims").json() == [], "a refused tool never runs"
    statuses = [(c["tool"], c["status"]) for c in _calls(client, pid)]
    assert ("drop_all_tables", "DENIED") in statuses and ("propose_claim", "DENIED") in statuses


def test_arguments_are_validated_and_cannot_switch_project(client: TestClient, session: Session) -> None:
    pid = _project(client)
    ctx = _ctx(pid, "search_sources")
    with pytest.raises(ToolInputError):
        registry.invoke(session, ctx, "search_sources", {"query": "x", "project_id": str(uuid4())})
    assert _calls(client, pid)[0]["status"] == "INVALID"


def test_reads_are_scoped_to_the_task_project(client: TestClient, session: Session) -> None:
    mine, other = _project(client), _project(client)
    _library(client, session, other, "Confidential passage about mentoring.")
    other_hypothesis = client.post(
        f"/api/v1/projects/{other}/hypotheses", json={"content": {"statement": "Other project's idea"}}
    ).json()
    ctx = _ctx(mine, "search_sources", "read_passages", "get_hypothesis")
    assert registry.invoke(session, ctx, "search_sources", {"query": "mentoring"})["hits"] == []

    foreign = registry.invoke(session, _ctx(other, "search_sources"), "search_sources", {"query": "mentoring"})
    chunk_id = foreign["hits"][0]["chunk_id"]
    assert registry.invoke(session, ctx, "read_passages", {"chunk_ids": [chunk_id]})["passages"] == []
    with pytest.raises(NotFoundError):
        registry.invoke(session, ctx, "get_hypothesis", {"hypothesis_id": other_hypothesis["id"]})
    assert _calls(client, mine)[0]["status"] == "ERROR"


def test_proposals_need_provenance_and_land_as_reviewable_states(client: TestClient, session: Session) -> None:
    pid = _project(client)
    args = {"statement": "Mentoring predicts retention", "claim_type": "FACTUAL_CLAIM"}
    with pytest.raises(ToolDeniedError, match="provenance"):
        registry.invoke(session, _ctx(pid, "propose_claim"), "propose_claim", args)
    out = registry.invoke(session, _ctx(pid, "propose_claim", action=True), "propose_claim", args)
    assert out["workflow_state"] == "PROPOSED"
    [claim] = client.get(f"/api/v1/projects/{pid}/claims").json()
    assert claim["statement_origin"] == "SYSTEM_INFERRED"
    assert claim["provenance"]["kind"] == "AI_GENERATED"
    ok = [c for c in _calls(client, pid) if c["status"] == "OK"]
    assert ok[0]["output_ids"] == [out["claim_id"]] and ok[0]["ai_request_id"]


def test_evidence_proposals_cite_project_passages_only(client: TestClient, session: Session) -> None:
    pid, other = _project(client), _project(client)
    passage = "Retention rose where mentoring was cut."
    _library(client, session, pid, passage)
    _library(client, session, other, "Foreign passage.")
    hypothesis = client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "H"}}).json()
    mine = registry.invoke(session, _ctx(pid, "search_sources"), "search_sources", {"query": "retention"})["hits"][0]
    foreign = registry.invoke(session, _ctx(other, "search_sources"), "search_sources", {"query": "foreign"})["hits"][0]
    ctx = _ctx(pid, "propose_evidence", action=True)
    base = {"target_type": "HYPOTHESIS", "target_id": hypothesis["id"], "role": "CONTRADICTS", "finding": "Counter"}
    out = registry.invoke(
        session, ctx, "propose_evidence", {**base, "chunk_id": mine["chunk_id"], "track": "CHALLENGE"}
    )
    assert out["status"] == "CANDIDATE"
    excerpt = client.get(f"/api/v1/sources/excerpts/{out['excerpt_id']}").json()
    assert excerpt["text"] == passage
    with pytest.raises(NotFoundError):
        registry.invoke(session, ctx, "propose_evidence", {**base, "chunk_id": foreign["chunk_id"]})


def test_orchestrator_tasks_act_only_through_logged_tools(client: TestClient, session: Session) -> None:
    pid = _project(client)
    _library(client, session, pid, "Retention rose where mentoring was cut in 2021.")
    hid = client.post(
        f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "Mentoring matters"}}
    ).json()["id"]
    mock_adapter.register(
        "plan_challenge", lambda _r: {"challenge_queries": ["retention mentoring"], "alternative_explanations": []}
    )
    mock_adapter.register(
        "assess_passages",
        lambda r: {
            "candidates": [
                {"passage_id": s.source_id, "role": "CONTRADICTS", "alternative_index": -1, "finding": "Counter"}
                for s in r.sections
                if s.kind == "retrieved_source"
            ],
            "alternative_support": [],
        },
    )
    body = {"task": "challenge", "target_type": "HYPOTHESIS", "target_id": hid, "profile": "mock"}
    job_id = client.post(f"/api/v1/projects/{pid}/ai-tasks", json=body).json()["id"]
    orchestrator.run(session, jobs.get_job(session, UUID(job_id)))
    calls = [c for c in _calls(client, pid) if c["job_id"] == job_id]
    assert {c["tool"] for c in calls} == {"search_sources", "read_passages", "propose_evidence"}
    assert all(c["status"] == "OK" for c in calls)
    assert all(c["ai_request_id"] for c in calls if c["kind"] == "PROPOSE")


def test_tool_call_log_is_append_only(client: TestClient, session: Session) -> None:
    pid = _project(client)
    registry.invoke(session, _ctx(pid, "search_sources"), "search_sources", {"query": "x"})
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text("UPDATE ai_tool_calls SET status = 'OK' WHERE project_id = :p"), {"p": pid})
