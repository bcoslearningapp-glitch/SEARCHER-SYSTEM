"""Whole-installation backup and restore (#58).

A migrated source database with committed research data is backed up, then restored into an empty database
and a fresh storage root. Ids, audit history and file checksums must come back identical.
"""

from __future__ import annotations

import io
import tarfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from research_api.config import get_settings
from research_api.main import create_app
from research_api.ops import backup
from research_api.platform.db import get_session
from tests.integration.conftest import alembic_config

SOURCE_DB = "research_backup_source"
TARGET_DB = "research_backup_target"
TABLES = ("projects", "claims", "audit_events", "research_events", "problem_frame_versions")


def _url(name: str) -> str:
    return make_url(get_settings().database_url).set(database=name).render_as_string(hide_password=False)


@pytest.fixture(scope="module")
def databases(engine: Engine) -> Iterator[tuple[str, str]]:
    """A migrated source database and an empty target database, both thrown away afterwards."""
    admin = create_engine(make_url(get_settings().database_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        for name in (SOURCE_DB, TARGET_DB):
            conn.execute(text(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)"))
            conn.execute(text(f"CREATE DATABASE {name}"))
    config = alembic_config()
    config.attributes["database_url"] = _url(SOURCE_DB)
    command.upgrade(config, "head")
    yield _url(SOURCE_DB), _url(TARGET_DB)
    with admin.connect() as conn:
        for name in (SOURCE_DB, TARGET_DB):
            conn.execute(text(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)"))
    admin.dispose()


def _seed(source_url: str) -> dict[str, Any]:
    """Committed research data created through the API against the source database."""
    source = create_engine(source_url)
    app = create_app()

    def _session() -> Iterator[Session]:
        with Session(bind=source) as session:
            yield session
            session.commit()

    app.dependency_overrides[get_session] = _session
    with TestClient(app) as client:
        project = client.post(
            "/api/v1/projects", json={"title": "Backed up", "initial_input": "x", "input_type": "IDEA"}
        ).json()
        claim = client.post(
            f"/api/v1/projects/{project['id']}/claims", json={"statement": "Kept", "claim_type": "OBSERVATION"}
        ).json()
    source.dispose()
    return {"project": project["id"], "claim": claim["id"]}


def _snapshot(url: str) -> dict[str, list[Any]]:
    eng = create_engine(url)
    with eng.connect() as conn:
        rows = {t: sorted(str(r[0]) for r in conn.execute(text(f"SELECT id FROM {t}"))) for t in TABLES}  # noqa: S608
    eng.dispose()
    return rows


def test_backup_restores_identical_ids_history_and_files(databases: tuple[str, str], tmp_path: Path) -> None:
    source_url, target_url = databases
    ids = _seed(source_url)
    storage = tmp_path / "storage"
    (storage / "sha256" / "ab").mkdir(parents=True)
    (storage / "sha256" / "ab" / "abc123").write_bytes(b"%PDF-1.4 source asset bytes")

    archive = backup.create_backup(tmp_path / "backups", database_url=source_url, storage_root=storage)
    manifest = backup.verify_backup(archive)
    assert manifest["schema_revision"] is not None

    restored_storage = tmp_path / "restored"
    backup.restore_backup(archive, database_url=target_url, storage_root=restored_storage)
    before, after = _snapshot(source_url), _snapshot(target_url)
    assert after == before
    assert ids["project"] in after["projects"] and ids["claim"] in after["claims"]
    assert after["audit_events"], "audit history comes back"
    assert (restored_storage / "sha256" / "ab" / "abc123").read_bytes() == b"%PDF-1.4 source asset bytes"


def test_restoring_over_existing_data_needs_replace(databases: tuple[str, str], tmp_path: Path) -> None:
    source_url, _ = databases
    archive = backup.create_backup(tmp_path, database_url=source_url, storage_root=tmp_path / "none")
    with pytest.raises(backup.BackupError, match="--replace"):
        backup.restore_backup(archive, database_url=source_url, storage_root=tmp_path / "s")
    backup.restore_backup(archive, database_url=source_url, storage_root=tmp_path / "s", replace=True)
    assert _snapshot(source_url)["projects"], "the replaced installation holds the backed-up data"


def test_a_tampered_archive_is_refused_before_anything_is_written(databases: tuple[str, str], tmp_path: Path) -> None:
    source_url, _ = databases
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "file.bin").write_bytes(b"original")
    archive = backup.create_backup(tmp_path, database_url=source_url, storage_root=storage)
    tampered = tmp_path / "tampered.tar"
    with tarfile.open(archive) as src, tarfile.open(tampered, "w") as dst:
        for member in src.getmembers():
            data = src.extractfile(member)
            if member.name == "storage/file.bin":
                member.size = len(b"modified")
                dst.addfile(member, io.BytesIO(b"modified"))
            else:
                dst.addfile(member, data)
    with pytest.raises(backup.BackupError, match="checksum"):
        backup.verify_backup(tampered)


def test_unsafe_entries_are_refused(tmp_path: Path) -> None:
    evil = tmp_path / "evil.tar"
    with tarfile.open(evil, "w") as archive:
        info = tarfile.TarInfo("../escape")
        info.size = 0
        archive.addfile(info, io.BytesIO(b""))
    with pytest.raises(backup.BackupError):
        backup.verify_backup(evil)
