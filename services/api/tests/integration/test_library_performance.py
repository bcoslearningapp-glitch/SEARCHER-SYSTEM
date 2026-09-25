"""Regression for the library listing's N+1 queries found by the #57 benchmark."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import event
from sqlalchemy.orm import Session

from research_api.modules.sources_library import service
from research_api.platform import queue


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


@contextmanager
def _count_queries(session: Session) -> Iterator[list[str]]:
    statements: list[str] = []
    connection = session.connection()

    def before(conn, cursor, statement, parameters, context, executemany) -> None:  # type: ignore[no-untyped-def]
        statements.append(statement)

    event.listen(connection, "before_cursor_execute", before)
    try:
        yield statements
    finally:
        event.remove(connection, "before_cursor_execute", before)


def test_listing_works_uses_a_constant_number_of_queries(client: TestClient, session: Session) -> None:
    pid = client.post("/api/v1/projects", json={"title": "L", "initial_input": "x", "input_type": "IDEA"}).json()["id"]
    for i in range(25):
        work = client.post("/api/v1/sources", json={"work": {"title": f"W{i}"}, "project_id": pid}).json()
        client.post(
            f"/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
            files={"file": (f"w{i}.txt", f"text {i}".encode(), "text/plain")},
        )
    with _count_queries(session) as statements:
        works = service.list_works(session, project_id=pid)
    assert len(works) == 25
    assert all(w.editions and w.editions[0].assets for w in works)
    assert len(statements) <= 3, f"{len(statements)} queries: editions and assets must be batch-loaded"
