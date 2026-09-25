"""Research Core Package round trip (issue #46, FR-PORT-001..006).

The import side runs against a second, freshly migrated database, so the round trip is real:
the same portable ids arrive in an environment that has never seen them.
"""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Iterator
from typing import Any
from uuid import UUID

import pytest
from alembic import command
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit.principal import local_owner
from research_api.modules.portability import service as portability
from research_api.modules.sources_library import ingestion
from research_api.platform import queue
from research_api.platform.errors import RuleViolationError
from tests.integration.conftest import alembic_config
from tests.integration.test_evidence_hypotheses import _accept, _excerpt
from tests.pdf_fixtures import make_pdf

TARGET_DB = "research_package_target"


@pytest.fixture(autouse=True)
def _no_broker(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(queue, "dispatch", lambda task, job_id: None)


@pytest.fixture(scope="module")
def target_engine(engine: Engine) -> Iterator[Engine]:
    """A second, empty, fully migrated database to import into."""
    url = make_url(get_settings().database_url)
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TARGET_DB}"))
        conn.execute(text(f"CREATE DATABASE {TARGET_DB}"))
    target_url = url.set(database=TARGET_DB).render_as_string(hide_password=False)
    config = alembic_config()
    config.attributes["database_url"] = target_url
    command.upgrade(config, "head")
    target = create_engine(target_url)
    yield target
    target.dispose()
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TARGET_DB} WITH (FORCE)"))
    admin.dispose()


def _project(client: TestClient, session: Session) -> dict[str, Any]:
    pid = str(
        client.post("/api/v1/projects", json={"title": "Portable", "initial_input": "x", "input_type": "IDEA"}).json()[
            "id"
        ]
    )
    claim = client.post(
        f"/api/v1/projects/{pid}/claims", json={"statement": "Mentoring drops", "claim_type": "OBSERVATION"}
    ).json()
    _, excerpt = _excerpt(client, pid, "Cohort study", "Mentoring declines sharply in the second year.")
    evidence = _accept(client, pid, ("CLAIM", claim["id"]), "SUPPORTS", excerpt, "SUPPORTED")
    assets = {}
    for title, portable in (("Open report", True), ("Licensed book", False)):
        work = client.post(
            "/api/v1/sources",
            json={"work": {"title": title}, "edition": {"portable_asset_allowed": portable}, "project_id": pid},
        ).json()
        asset = client.post(
            f"/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
            files={"file": (f"{title}.pdf", make_pdf([f"{title} page one"]), "application/pdf")},
        ).json()
        ingestion.ingest_asset(session, UUID(asset["id"]))
        assets[portable] = asset["id"]
    client.post(f"/api/v1/projects/{pid}/hypotheses", json={"content": {"statement": "Mentoring matters"}})
    return {"pid": pid, "claim": claim["id"], "excerpt": excerpt, "evidence": evidence["id"], "assets": assets}


def _download(client: TestClient, pid: str) -> bytes:
    response = client.get(f"/api/v1/projects/{pid}/package")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    return response.content


def _rezip(data: bytes, change: dict[str, bytes]) -> bytes:
    source = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        for name in source.namelist():
            archive.writestr(name, change.get(name, source.read(name)))
    return out.getvalue()


def test_round_trip_preserves_identity_and_never_upgrades_trust(
    client: TestClient, session: Session, target_engine: Engine
) -> None:
    project = _project(client, session)
    data = _download(client, project["pid"])
    archive = zipfile.ZipFile(io.BytesIO(data))
    manifest = json.loads(archive.read("manifest.json"))
    assert contract_errors("package-manifest", manifest) == []
    assert manifest["excluded_assets"] == [
        {"asset_id": project["assets"][False], "reason": "The edition's licence/portability policy withholds the file"}
    ]
    assert not any(e["path"].startswith("entities/background_jobs") for e in manifest["entries"])
    pages = [json.loads(line) for line in archive.read("entities/source_pages.jsonl").decode().splitlines()]
    assert {p["asset_id"] for p in pages} == {project["assets"][True]}, "withheld files do not leak as derived text"

    with Session(target_engine) as target:
        report = portability.import_project(target, local_owner(), data)
        target.commit()
        assert report.project_id == UUID(project["pid"])
        assert report.metadata_only_assets == [project["assets"][False]]
        assert report.assets_restored == 1

        def one(sql: str, **params: Any) -> Any:
            return target.execute(text(sql), params).one()

        assert one("SELECT statement FROM claims WHERE id = :id", id=project["claim"])[0] == "Mentoring drops"
        evidence = one("SELECT status, excerpt_id FROM evidence WHERE id = :id", id=project["evidence"])
        assert evidence == ("ACCEPTED", UUID(project["excerpt"]))
        excerpt = one("SELECT text, verification_state FROM source_excerpts WHERE id = :id", id=project["excerpt"])
        original = session.execute(
            text("SELECT text, verification_state FROM source_excerpts WHERE id = :id"), {"id": project["excerpt"]}
        ).one()
        assert tuple(excerpt) == tuple(original), "exact text and verification arrive unchanged, never upgraded"
        withheld = one("SELECT available_in_environment FROM source_assets WHERE id = :id", id=project["assets"][False])
        restored = one("SELECT available_in_environment FROM source_assets WHERE id = :id", id=project["assets"][True])
        assert (withheld[0], restored[0]) == (False, True), (
            "a withheld file makes the source metadata-only, not deleted"
        )
        audit = one(
            "SELECT count(*) FROM audit_events WHERE project_id = :id AND action = 'project.import'", id=project["pid"]
        )
        assert audit[0] == 1

        with pytest.raises(Exception, match="already exists"):
            portability.import_project(target, local_owner(), data)


def test_tampered_or_newer_packages_are_refused(client: TestClient, session: Session) -> None:
    project = _project(client, session)
    data = _download(client, project["pid"])
    tampered = _rezip(data, {"entities/claims.jsonl": b'{"id": "00000000-0000-0000-0000-000000000000"}\n'})
    with pytest.raises(RuleViolationError, match="checksum"):
        portability.import_project(session, local_owner(), tampered)
    manifest = json.loads(zipfile.ZipFile(io.BytesIO(data)).read("manifest.json"))
    newer = _rezip(data, {"manifest.json": json.dumps({**manifest, "schema_revision": "9999"}).encode()})
    with pytest.raises(RuleViolationError, match="newer schema"):
        portability.import_project(session, local_owner(), newer)
    extra = io.BytesIO(data)
    with zipfile.ZipFile(extra, "a") as archive:
        archive.writestr("entities/extra.jsonl", "{}\n")
    with pytest.raises(RuleViolationError, match="not listed"):
        portability.import_project(session, local_owner(), extra.getvalue())
    conflict = client.post("/api/v1/packages/import", files={"file": ("p.zip", data, "application/zip")})
    assert conflict.status_code == 409, "a package never overwrites an existing project"
