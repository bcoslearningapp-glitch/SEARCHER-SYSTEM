from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from research_api.contracts.enums import ActorKind, ActorRole
from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit import service
from research_api.modules.governance_audit.schemas import Actor, AuditEntry, ResearchEventEntry

HUMAN = Actor(kind=ActorKind.HUMAN, id="local-owner", role=ActorRole.RESEARCHER)


def _entry(project_id=None) -> AuditEntry:  # type: ignore[no-untyped-def]
    return AuditEntry(
        project_id=project_id or uuid4(),
        action="problem_frame.approve",
        entity_type="ProblemFrame",
        entity_id=uuid4(),
        actor=HUMAN,
        previous_state={"status": "DRAFT"},
        new_state={"status": "APPROVED"},
        reason="baseline sufficient",
    )


def test_recorded_audit_event_round_trips_to_contract(session: Session) -> None:
    record = service.record_audit(session, _entry())
    out = service.to_out(record)
    assert out.versions.methodology_version == "1.0.0"
    assert contract_errors("event.AuditEvent", out.to_contract()) == []


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_events SET reason = 'rewritten'",
        "DELETE FROM audit_events",
        "TRUNCATE audit_events",
        "UPDATE research_events SET event_type = 'Rewritten'",
        "DELETE FROM research_events",
    ],
)
def test_event_tables_are_append_only(session: Session, statement: str) -> None:
    service.record_audit(session, _entry())
    service.record_research_event(session, ResearchEventEntry(event_type="ProblemFrameApproved", actor=HUMAN))
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(text(statement))


def test_database_rejects_ai_audit_without_provenance(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ai_provenance"), session.begin_nested():
        session.execute(
            text(
                "INSERT INTO audit_events (id, occurred_at, actor_kind, actor_id, core_schema_version,"
                " methodology_version, constitution_version, action)"
                " VALUES (gen_random_uuid(), now(), 'AI', 'x', '0.1.0', '1.0.0', '1.0.0', 'a.b')"
            )
        )


def test_audit_api_filters_by_project(session: Session, client: TestClient) -> None:
    mine, other = uuid4(), uuid4()
    service.record_audit(session, _entry(mine))
    service.record_audit(session, _entry(other))
    response = client.get("/api/v1/audit-events", params={"project_id": str(mine)})
    assert response.status_code == 200
    body = response.json()
    assert [e["project_id"] for e in body] == [str(mine)]
