"""Regression: the request's transaction commits before the response is sent.

With FastAPI's default request scope a client could observe 2xx before the
write was durable (seen as a cross-request race in E2E), and a failed commit
would surface only after success had been reported.
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.testclient import TestClient

from research_api.platform.db import DBSession, get_session


class _FailingCommitSession:
    committed = False


def _failing_session() -> Iterator[_FailingCommitSession]:
    yield _FailingCommitSession()
    raise RuntimeError("commit failed")


def test_failed_commit_is_reported_to_the_client() -> None:
    app = FastAPI()

    @app.post("/write", status_code=201)
    def write(db: DBSession) -> dict[str, bool]:
        return {"ok": True}

    app.dependency_overrides[get_session] = _failing_session
    response = TestClient(app, raise_server_exceptions=False).post("/write")
    assert response.status_code == 500
