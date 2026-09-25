"""Research Core Package export and import (PRD §45, FR-PORT-001..006, Core §68-69, SEC-010).

A package is a zip file with:
- `manifest.json`: identity, versions, schema revision, and a SHA-256 for every entry;
- `entities/<table>.jsonl`: one row per line, stable portable ids kept as they are;
- `assets/<sha256>`: digital asset bytes, only where the edition's portability/licence allows.

Import rules:
- Checksums and the manifest contract are verified before anything is written.
- The package's schema revision must not be newer than this installation's.
- Only known tables and columns are accepted.
- A project that already exists here is never overwritten.

Import never upgrades trust (FR-PORT-006):
- Shared library rows that already exist here are left exactly as they are.
- A foundational text arrives STAGED and needs this environment's own approval.
- An asset is available only if its bytes arrived and matched their checksum. Otherwise its source is
  metadata-only here, and neither the source nor its relationships are deleted (FR-PORT-004).
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, DateTime, Table, Uuid, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from research_api import __version__
from research_api.config import get_settings
from research_api.contracts.enums import CONTRACT_SCHEMA_VERSION
from research_api.contracts.schemas import contract_errors
from research_api.modules.governance_audit.principal import Principal
from research_api.platform.db import Base
from research_api.platform.errors import ConflictError, RuleViolationError
from research_api.platform.storage import StorageError, get_store

MANIFEST = "manifest.json"
# Operational records that describe this installation rather than the research.
EXCLUDED = frozenset({"background_jobs", "knowledge_reuses"})
AUDIT = frozenset(
    {"audit_events", "research_events", "approvals", "quality_gate_evaluations", "ai_requests", "ai_tool_calls"}
)
# Library and foundational rows can be shared with other projects; an existing row here always wins.
SHARED = frozenset(
    {
        "source_works",
        "source_editions",
        "source_assets",
        "source_pages",
        "source_chunks",
        "source_excerpts",
        "source_lineage",
        "foundational_sources",
        "hadith_records",
    }
)
# Derived text of an asset travels only with the asset's bytes (it is the content).
WITH_BYTES = frozenset({"source_pages", "source_chunks"})
MAX_PACKAGE_BYTES = 1024 * 1024 * 1024
_PATH = re.compile(r"^(?!/)(?!.*\.\.)[A-Za-z0-9._/-]+$")


def _tables() -> dict[str, Table]:
    return {t.name: t for t in Base.metadata.sorted_tables}


def _columns(table: Table) -> list[Column[Any]]:
    return [c for c in table.columns if c.computed is None]


def _encode(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _decode(column: Column[Any], value: Any) -> Any:
    if value is None:
        return None
    if isinstance(column.type, Uuid):
        return UUID(value)
    if isinstance(column.type, DateTime):
        return datetime.fromisoformat(value)
    if isinstance(column.type, Date):
        return date.fromisoformat(value)
    return value


def _schema_revision(session: Session) -> str:
    return str(session.execute(text("SELECT version_num FROM alembic_version")).scalar_one())


# --- export ---


@dataclass
class _Collected:
    rows: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    ids: dict[str, set[Any]] = field(default_factory=lambda: defaultdict(set))

    def add(self, table: Table, row: dict[str, Any]) -> None:
        key = row.get("id", tuple(row[c.name] for c in table.primary_key.columns))
        if key in self.ids[table.name]:
            return
        self.ids[table.name].add(key)
        self.rows[table.name].append(row)


def _select(session: Session, table: Table, where: Any) -> list[dict[str, Any]]:
    cols = _columns(table)
    return [dict(zip([c.name for c in cols], r, strict=True)) for r in session.execute(select(*cols).where(where))]


def _collect_project(session: Session, project_id: UUID, out: _Collected) -> None:
    """Rows owned by the project, then their children through foreign keys (in dependency order)."""
    tables = _tables()
    for row in _select(session, tables["projects"], tables["projects"].c.id == project_id):
        out.add(tables["projects"], row)
    for table in tables.values():
        if table.name in EXCLUDED | SHARED or table.name == "projects":
            continue
        if "project_id" in table.c:
            for row in _select(session, table, table.c.project_id == project_id):
                out.add(table, row)
            continue
        for fk in table.foreign_keys:
            parent = fk.column.table.name
            if parent in SHARED or parent == "projects" or not out.ids[parent]:
                continue
            for row in _select(session, table, fk.parent.in_(out.ids[parent])):
                out.add(table, row)


def _referenced(out: _Collected) -> tuple[set[Any], set[Any], set[Any], set[Any]]:
    """Works, editions, excerpts and Hadith records the project's rows point at."""
    works = {r["work_id"] for r in out.rows["project_sources"]}
    works |= {r["suspected_work_id"] for r in out.rows["source_leads"] if r.get("suspected_work_id")}
    editions = {r["edition_id"] for r in out.rows["source_access_requests"]}
    excerpts = {r["excerpt_id"] for r in out.rows["evidence"]}
    excerpts |= {r["verified_by_excerpt_id"] for r in out.rows["source_leads"] if r.get("verified_by_excerpt_id")}
    excerpts |= {r["source_excerpt_id"] for r in out.rows["reference_entries"] if r.get("source_excerpt_id")}
    hadith = {r["hadith_record_id"] for r in out.rows["reference_entries"] if r.get("hadith_record_id")}
    return works, editions, excerpts, hadith


def _collect_library(session: Session, out: _Collected) -> set[UUID]:
    """The library records the project uses. Returns the assets whose files may travel."""
    t = _tables()
    works, editions, excerpts, hadith = _referenced(out)
    requests = {r["id"] for r in out.rows["source_access_requests"]}
    excerpt_rows = _select(session, t["source_excerpts"], t["source_excerpts"].c.id.in_(excerpts))
    excerpt_rows += _select(session, t["source_excerpts"], t["source_excerpts"].c.access_request_id.in_(requests))
    editions |= {r["edition_id"] for r in excerpt_rows}
    works |= {r["work_id"] for r in _select(session, t["source_editions"], t["source_editions"].c.id.in_(editions))}
    hadith_rows = _select(session, t["hadith_records"], t["hadith_records"].c.id.in_(hadith))
    foundational = {r["foundational_source_id"] for r in hadith_rows}
    foundational_rows = _select(session, t["foundational_sources"], t["foundational_sources"].c.id.in_(foundational))
    works |= {r["work_id"] for r in foundational_rows}
    for name, where in (
        ("source_works", t["source_works"].c.id.in_(works)),
        ("source_editions", t["source_editions"].c.work_id.in_(works)),
    ):
        for row in _select(session, t[name], where):
            out.add(t[name], row)
    for row in _select(session, t["source_lineage"], t["source_lineage"].c.from_work_id.in_(works)):
        if row["to_work_id"] in works:
            out.add(t["source_lineage"], row)
    for row in _select(session, t["source_assets"], t["source_assets"].c.edition_id.in_(out.ids["source_editions"])):
        out.add(t["source_assets"], row)
    for name, rows in (
        ("source_excerpts", excerpt_rows),
        ("foundational_sources", foundational_rows),
        ("hadith_records", hadith_rows),
    ):
        for row in rows:
            out.add(t[name], row)
    portable_editions = {r["id"] for r in out.rows["source_editions"] if r.get("portable_asset_allowed")}
    portable = {r["id"] for r in out.rows["source_assets"] if r["edition_id"] in portable_editions}
    for name in sorted(WITH_BYTES):
        for row in _select(session, t[name], t[name].c.asset_id.in_(portable)):
            out.add(t[name], row)
    return portable


def _collect(session: Session, project_id: UUID) -> tuple[_Collected, set[UUID]]:
    out = _Collected()
    _collect_project(session, project_id, out)
    return out, _collect_library(session, out)


def export_package(
    session: Session, principal: Principal, project_id: UUID, actor: dict[str, Any]
) -> tuple[bytes, str]:
    collected, portable_assets = _collect(session, project_id)
    if not collected.rows["projects"]:
        raise RuleViolationError("project not found")
    buffer = io.BytesIO()
    entries: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    counts: dict[str, int] = {}
    store = get_store()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for table in Base.metadata.sorted_tables:
            rows = collected.rows.get(table.name)
            if not rows:
                continue
            body = "".join(json.dumps({k: _encode(v) for k, v in r.items()}, ensure_ascii=False) + "\n" for r in rows)
            path = f"entities/{table.name}.jsonl"
            archive.writestr(path, body)
            kind = "audit" if table.name in AUDIT else "entities"
            entries.append(
                {
                    "path": path,
                    "sha256": hashlib.sha256(body.encode()).hexdigest(),
                    "content_type": kind,
                    "entity_type": table.name,
                }
            )
            counts[table.name] = len(rows)
        for asset in collected.rows.get("source_assets", []):
            if not asset.get("storage_key"):
                continue
            if asset["id"] not in portable_assets:
                excluded.append(
                    {
                        "asset_id": str(asset["id"]),
                        "reason": "The edition's licence/portability policy withholds the file",
                    }
                )
                continue
            try:
                data = store.read(asset["storage_key"])
            except StorageError:
                excluded.append(
                    {"asset_id": str(asset["id"]), "reason": "The file is not available in the exporting environment"}
                )
                continue
            path = f"assets/{asset['sha256']}"
            if path not in {e["path"] for e in entries}:
                archive.writestr(path, data)
                entries.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "content_type": "asset"})
        settings = get_settings()
        manifest = {
            "package_format": "research-core-package",
            "package_id": str(uuid4()),
            "project_id": str(project_id),
            "exported_at": datetime.now().astimezone().isoformat(),
            "exported_by": actor,
            "producer": {"product": "PRODUCT_B", "version": __version__},
            "versions": {
                "core_schema_version": CONTRACT_SCHEMA_VERSION,
                "methodology_version": settings.methodology_version,
                "constitution_version": settings.constitution_version,
            },
            "schema_revision": _schema_revision(session),
            "counts": counts,
            "entries": entries,
            "excluded_assets": excluded,
        }
        archive.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2))
    return buffer.getvalue(), str(manifest["package_id"])


# --- import ---


@dataclass
class ImportReport:
    package_id: str
    project_id: UUID
    inserted: dict[str, int]
    kept_existing: dict[str, int]
    assets_restored: int
    metadata_only_assets: list[str]
    staged_foundational: list[str]
    trust_notes: list[str]


def _read(data: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    if len(data) > MAX_PACKAGE_BYTES:
        raise RuleViolationError("package is too large")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise RuleViolationError("not a Research Core Package (zip expected)") from exc
    total = sum(i.file_size for i in archive.infolist())
    if total > MAX_PACKAGE_BYTES:
        raise RuleViolationError("package expands beyond the size limit")
    names = set(archive.namelist())
    if MANIFEST not in names:
        raise RuleViolationError("package has no manifest")
    manifest = json.loads(archive.read(MANIFEST))
    errors = contract_errors("package-manifest", manifest)
    if errors:
        raise RuleViolationError("package manifest is invalid", errors=errors[:10])
    files: dict[str, bytes] = {}
    for entry in manifest["entries"]:
        path = entry["path"]
        if not _PATH.match(path) or path not in names:
            raise RuleViolationError("package entry is missing or unsafe", path=path)
        content = archive.read(path)
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise RuleViolationError("package checksum mismatch; nothing was imported", path=path)
        files[path] = content
    unlisted = names - {MANIFEST} - set(files)
    if unlisted:
        raise RuleViolationError("package contains files not listed in its manifest", files=sorted(unlisted)[:10])
    return manifest, files


def _parse(manifest: dict[str, Any], files: dict[str, bytes]) -> dict[str, list[dict[str, Any]]]:
    tables = _tables()
    parsed: dict[str, list[dict[str, Any]]] = {}
    for entry in manifest["entries"]:
        if entry["content_type"] == "asset":
            continue
        name = entry.get("entity_type") or ""
        if name not in tables or name in EXCLUDED:
            raise RuleViolationError("package contains an unknown entity type", entity_type=name)
        columns = {c.name: c for c in _columns(tables[name])}
        rows = []
        for line in files[entry["path"]].decode().splitlines():
            raw = json.loads(line)
            unknown = set(raw) - set(columns)
            if unknown:
                raise RuleViolationError("package rows have unknown fields", entity_type=name, fields=sorted(unknown))
            rows.append({k: _decode(columns[k], v) for k, v in raw.items()})
        parsed[name] = rows
    return parsed


def _restore_assets(parsed: dict[str, list[dict[str, Any]]], files: dict[str, bytes], report: ImportReport) -> None:
    """An asset is available here only if its bytes arrived intact (FR-PORT-004)."""
    store = get_store()
    restored: set[UUID] = set()
    for row in parsed.get("source_assets", []):
        content = files.get(f"assets/{row.get('sha256') or ''}")
        if content is not None and hashlib.sha256(content).hexdigest() == row["sha256"]:
            row["storage_key"] = store.put(content).key
            row["available_in_environment"] = True
            restored.add(row["id"])
        else:
            row["storage_key"] = None
            row["available_in_environment"] = False
            report.metadata_only_assets.append(str(row["id"]))
    report.assets_restored = len(restored)
    for name in WITH_BYTES:
        parsed[name] = [r for r in parsed.get(name, []) if r["asset_id"] in restored]


def _no_trust_upgrade(session: Session, parsed: dict[str, list[dict[str, Any]]], report: ImportReport) -> None:
    """Foundational texts need local approval; links to projects absent here are dropped."""
    for row in parsed.get("foundational_sources", []):
        row["status"] = "STAGED"
        for key in ("approved_by_kind", "approved_by_id", "approved_at"):
            if key in row:
                row[key] = None
        report.staged_foundational.append(str(row["id"]))
    projects = _tables()["projects"]
    for row in parsed.get("projects", []):
        forked = row.get("forked_from_project_id")
        if forked and not session.execute(select(projects.c.id).where(projects.c.id == forked)).first():
            row["forked_from_project_id"] = None


def _insert(session: Session, parsed: dict[str, list[dict[str, Any]]], report: ImportReport) -> None:
    for table in Base.metadata.sorted_tables:
        rows = parsed.get(table.name)
        if not rows:
            continue
        statement = insert(table)
        if table.name in SHARED:
            result = session.execute(statement.on_conflict_do_nothing().returning(*table.primary_key.columns), rows)
            inserted = len(result.all())
            report.kept_existing[table.name] = len(rows) - inserted
        else:
            session.execute(statement, rows)
            inserted = len(rows)
        report.inserted[table.name] = inserted


def import_package(session: Session, data: bytes) -> ImportReport:
    manifest, files = _read(data)
    local_revision = _schema_revision(session)
    if manifest.get("schema_revision", "0000") > local_revision:
        raise RuleViolationError(
            "package was written by a newer schema; upgrade this installation first",
            package=manifest.get("schema_revision"),
            local=local_revision,
        )
    project_id = UUID(manifest["project_id"])
    projects = _tables()["projects"]
    if session.execute(select(projects.c.id).where(projects.c.id == project_id)).first():
        raise ConflictError(
            "this project already exists here; a package never overwrites a project", project_id=str(project_id)
        )
    parsed = _parse(manifest, files)
    report = ImportReport(manifest["package_id"], project_id, {}, {}, 0, [], [], [])
    _restore_assets(parsed, files, report)
    _no_trust_upgrade(session, parsed, report)
    _insert(session, parsed, report)
    report.trust_notes = [
        "Existing library records here were kept unchanged; the package did not raise their verification.",
        "Foundational texts arrive STAGED and need approval in this environment.",
        f"{len(report.metadata_only_assets)} asset(s) arrived without files and are metadata-only here.",
    ]
    session.flush()
    return report
