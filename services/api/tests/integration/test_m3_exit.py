"""PRD Phase 3 exit criteria as executable checks (issue #30).

- same research task can run with either provider;
- provider switch does not alter stored schema;
- no provider receives DB credentials;
- counter-evidence track demonstrably runs (test_orchestrator / test_ai_tools challenge flows).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session

from research_api.config import Settings, get_settings
from research_api.contracts.schemas import contract_errors
from research_api.modules.ai_gateway import mock_adapter, prompting
from research_api.modules.ai_gateway import profiles as registry
from research_api.modules.ai_gateway.base import ModelProfile, Section, StructuredRequest
from research_api.modules.ai_tools.registry import TOOLS
from research_api.modules.research_orchestrator import service as orchestrator
from research_api.platform import jobs, queue
from tests.contract_helpers import as_contract

_original_profiles = registry.profiles


def _two_providers(settings: Settings) -> dict[str, ModelProfile]:
    found = _original_profiles(settings)
    # A second provider behind the same neutral interface, as Anthropic and OpenAI are in production.
    found["mock-b"] = replace(found["mock"], name="mock-b", model="mock-structured-2")
    return found


@pytest.fixture(autouse=True)
def _providers(monkeypatch: MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("AI_MOCK_ENABLED", "true")
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)
    monkeypatch.setattr(registry, "profiles", _two_providers)
    get_settings.cache_clear()
    registry.reset_cache()
    yield
    mock_adapter.STATE.responders.clear()
    get_settings.cache_clear()
    registry.reset_cache()


def _assumptions_with(client: TestClient, session: Session, profile: str) -> list[dict[str, Any]]:
    body = {"title": "M3", "initial_input": "Mentors keep apprentices.", "input_type": "RAW_QUESTION"}
    pid = client.post("/api/v1/projects", json=body).json()["id"]
    task = {"task": "detect_assumptions", "profile": profile}
    job_id = client.post(f"/api/v1/projects/{pid}/ai-tasks", json=task).json()["id"]
    orchestrator.run(session, jobs.get_job(session, UUID(job_id)))
    return list(client.get(f"/api/v1/projects/{pid}/assumptions").json())


def test_same_task_on_either_provider_stores_the_same_schema(client: TestClient, session: Session) -> None:
    mock_adapter.register(
        "detect_assumptions",
        lambda _r: {"assumptions": [{"statement": "Mentors are available", "criticality": "HIGH", "rationale": "r"}]},
    )
    [a] = _assumptions_with(client, session, "mock")
    [b] = _assumptions_with(client, session, "mock-b")
    for item in (a, b):
        assert contract_errors("claims.Assumption", as_contract(item, drop=frozenset({"created_at"}))) == []
    assert set(a) == set(b)
    assert {k: a[k] for k in ("statement", "origin", "criticality", "status")} == {
        k: b[k] for k in ("statement", "origin", "criticality", "status")
    }
    # The provider/model appears only in provenance, never in the stored research schema.
    assert a["provenance"]["ai_action"]["model"] == "mock-structured-1"
    assert b["provenance"]["ai_action"]["model"] == "mock-structured-2"


def test_no_provider_receives_database_credentials() -> None:
    configured = get_settings().database_url
    distinctive = "postgresql+psycopg://svc:Zq9-Unique-Secret@db:5432/research"
    for dsn in (configured, distinctive):
        request = StructuredRequest(
            "t", "t@1", "Summarise.", [Section("user_input", "Pasted", f"connect with {dsn}")], {"type": "object"}
        )
        outbound = prompting.system_prompt(request) + prompting.user_prompt(request)
        credentials = dsn.split("://", 1)[1].split("@", 1)[0]
        assert f"{credentials}@" not in outbound, "user:password must be redacted before leaving the machine"
    assert "Zq9-Unique-Secret" not in outbound
    forbidden = ("sql", "query_db", "file", "path", "shell", "exec", "credential")
    for tool in TOOLS.values():
        assert not any(f in tool.name for f in forbidden), tool.name
        assert not any(f in key for key in tool.input_schema.get("properties", {}) for f in ("sql", "path", "dsn"))
