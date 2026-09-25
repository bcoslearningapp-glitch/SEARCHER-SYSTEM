"""Whole-installation backup and restore (PRD Phase 6, #58).

A backup is one uncompressed tar archive:
- `database.dump` is a `pg_dump` custom-format dump, which is already compressed;
- `storage/...` holds every file under the storage root (source assets and their derived files);
- `manifest.json` is written last. It records the format, the time, the schema revision, and the SHA-256
  and size of every other entry.

Restore verifies the whole archive before it writes anything. Checks: every entry is listed, has a safe
path, is a regular file and matches its checksum. Restoring over an installation that already holds data is
destructive (SEC-009), so it needs an explicit `--replace`.

This complements the per-project Research Core Package (ADR-022). The package moves one project between
installations; a backup recovers the whole installation, including its audit history and settings rows.
Remote cloud-workspace copies are not included; their manifest is in the database.

Usage (in the API container, or anywhere with PostgreSQL 16 client tools and the same settings):
    python -m research_api.ops.backup create --out /data/backups
    python -m research_api.ops.backup verify /data/backups/product-b-backup-<time>.tar
    python -m research_api.ops.backup restore /data/backups/product-b-backup-<time>.tar [--replace]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from research_api import __version__
from research_api.config import get_settings

FORMAT = "product-b-backup"
FORMAT_VERSION = 1
MANIFEST = "manifest.json"
DATABASE = "database.dump"
_CHUNK = 1024 * 1024
_SAFE = re.compile(r"^storage/(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$")


class BackupError(Exception):
    """The backup cannot be created, verified or restored; nothing further was changed."""


@dataclass(frozen=True)
class Entry:
    path: str
    sha256: str
    bytes: int


def _pg_env(database_url: str) -> tuple[dict[str, str], str]:
    """libpq settings for the database. The password goes in the environment, never on the command line."""
    url = make_url(database_url)
    env = dict(os.environ)
    for key, value in (("PGHOST", url.host), ("PGPORT", url.port), ("PGUSER", url.username)):
        if value is not None:
            env[key] = str(value)
    if url.password is not None:
        env["PGPASSWORD"] = str(url.password)
    return env, str(url.database)


def _run(args: list[str], env: dict[str, str]) -> None:
    tool = shutil.which(args[0])
    if tool is None:
        raise BackupError(f"{args[0]} is not installed; PostgreSQL 16 client tools are required")
    result = subprocess.run([tool, *args[1:]], env=env, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode != 0:
        raise BackupError(f"{args[0]} failed: {result.stderr.strip()[-2000:]}")


def _digest(path: Path) -> tuple[str, int]:
    sha = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            sha.update(chunk)
            size += len(chunk)
    return sha.hexdigest(), size


def _schema_revision(database_url: str) -> str | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            if conn.execute(text("SELECT to_regclass('public.alembic_version')")).scalar() is None:
                return None
            return str(conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one())
    finally:
        engine.dispose()


def create_backup(out_dir: Path, *, database_url: str, storage_root: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    created = datetime.now(UTC)
    target = out_dir / f"product-b-backup-{created.strftime('%Y%m%dT%H%M%SZ')}.tar"
    env, dbname = _pg_env(database_url)
    entries: list[Entry] = []
    with tempfile.TemporaryDirectory() as tmp:
        dump = Path(tmp) / DATABASE
        _run(["pg_dump", "--format=custom", "--no-owner", "--no-privileges", f"--file={dump}", dbname], env)
        partial = target.with_suffix(".tar.partial")
        with tarfile.open(partial, "w") as archive:
            sha, size = _digest(dump)
            archive.add(dump, arcname=DATABASE)
            entries.append(Entry(DATABASE, sha, size))
            root = storage_root.resolve()
            if root.is_dir():
                for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
                    name = f"storage/{path.relative_to(root).as_posix()}"
                    if not _SAFE.fullmatch(name):
                        raise BackupError(f"unexpected file name in storage: {path.name!r}")
                    sha, size = _digest(path)
                    archive.add(path, arcname=name)
                    entries.append(Entry(name, sha, size))
            manifest = {
                "format": FORMAT,
                "format_version": FORMAT_VERSION,
                "created_at": created.isoformat(),
                "app_version": __version__,
                "schema_revision": _schema_revision(database_url),
                "entries": [e.__dict__ for e in entries],
            }
            data = json.dumps(manifest, indent=2).encode()
            info = tarfile.TarInfo(MANIFEST)
            info.size = len(data)
            info.mtime = int(created.timestamp())
            archive.addfile(info, io.BytesIO(data))
        partial.replace(target)
    return target


def _read_manifest(archive: tarfile.TarFile, names: list[str]) -> dict[str, object]:
    if len(names) != len(set(names)):
        raise BackupError("the archive contains duplicate entries")
    if MANIFEST not in names:
        raise BackupError("the archive has no manifest")
    manifest_file = archive.extractfile(MANIFEST)
    if manifest_file is None:
        raise BackupError("the manifest is not a regular file")
    try:
        manifest = json.loads(manifest_file.read())
    except ValueError as exc:
        raise BackupError("the manifest is not valid JSON") from exc
    if manifest.get("format") != FORMAT or manifest.get("format_version") != FORMAT_VERSION:
        raise BackupError("unsupported backup format")
    return dict(manifest)


def _check_member(archive: tarfile.TarFile, member: tarfile.TarInfo, expected: dict[str, object]) -> None:
    if not member.isfile() or (member.name != DATABASE and not _SAFE.fullmatch(member.name)):
        raise BackupError(f"unsafe archive entry: {member.name!r}")
    handle = archive.extractfile(member)
    if handle is None:
        raise BackupError(f"unreadable archive entry: {member.name!r}")
    sha = hashlib.sha256()
    size = 0
    while chunk := handle.read(_CHUNK):
        sha.update(chunk)
        size += len(chunk)
    if sha.hexdigest() != expected["sha256"] or size != expected["bytes"]:
        raise BackupError(f"checksum mismatch for {member.name}")


def verify_backup(path: Path) -> dict[str, object]:
    """Check every entry against the manifest. Returns the manifest."""
    try:
        with tarfile.open(path, "r") as archive:
            members = archive.getmembers()
            manifest = _read_manifest(archive, [m.name for m in members])
            listed = {e["path"]: e for e in manifest["entries"]}  # type: ignore[attr-defined]
            if {m.name for m in members} - {MANIFEST} != set(listed):
                raise BackupError("archive entries do not match the manifest")
            if DATABASE not in listed:
                raise BackupError("the archive has no database dump")
            for member in members:
                if member.name != MANIFEST:
                    _check_member(archive, member, listed[member.name])
    except (OSError, tarfile.TarError) as exc:
        raise BackupError("not a readable backup archive") from exc
    return manifest


def _storage_conflicts(manifest: dict[str, object], root: Path) -> list[str]:
    conflicts = []
    for entry in manifest["entries"]:  # type: ignore[attr-defined]
        if entry["path"] == DATABASE:
            continue
        target = root / PurePosixPath(entry["path"]).relative_to("storage")
        if target.exists() and _digest(target)[0] != entry["sha256"]:
            conflicts.append(entry["path"])
    return conflicts


def restore_backup(path: Path, *, database_url: str, storage_root: Path, replace: bool = False) -> dict[str, object]:
    manifest = verify_backup(path)
    occupied = _schema_revision(database_url) is not None
    root = storage_root.resolve()
    with tarfile.open(path, "r") as archive:
        conflicts = _storage_conflicts(manifest, root)
        if (occupied or conflicts) and not replace:
            raise BackupError(
                "the target installation already holds data; restoring over it is destructive and needs --replace"
            )
        env, dbname = _pg_env(database_url)
        with tempfile.TemporaryDirectory() as tmp:
            archive.extract(DATABASE, tmp, filter="data")
            args = ["pg_restore", "--no-owner", "--no-privileges", "--single-transaction", "--exit-on-error"]
            if occupied:
                args += ["--clean", "--if-exists"]
            _run([*args, f"--dbname={dbname}", str(Path(tmp) / DATABASE)], env)
        for member in archive.getmembers():
            if member.name in (MANIFEST, DATABASE):
                continue
            target = (root / PurePosixPath(member.name).relative_to("storage")).resolve()
            if root not in target.parents:
                raise BackupError(f"entry escapes the storage root: {member.name!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise BackupError(f"unreadable archive entry: {member.name!r}")
            with target.open("wb") as out:
                shutil.copyfileobj(source, out, _CHUNK)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research_api.ops.backup", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="write a backup archive")
    create.add_argument("--out", type=Path, required=True)
    verify = commands.add_parser("verify", help="check an archive against its manifest")
    verify.add_argument("archive", type=Path)
    restore = commands.add_parser("restore", help="restore an archive into this installation")
    restore.add_argument("archive", type=Path)
    restore.add_argument("--replace", action="store_true", help="overwrite an installation that already holds data")
    args = parser.parse_args(argv)
    settings = get_settings()
    try:
        if args.command == "create":
            archive = create_backup(args.out, database_url=settings.database_url, storage_root=settings.storage_root)
            sys.stdout.write(f"{archive}\n")
        elif args.command == "verify":
            manifest = verify_backup(args.archive)
            sys.stdout.write(f"ok: {len(manifest['entries'])} entries, schema {manifest['schema_revision']}\n")  # type: ignore[arg-type]
        else:
            manifest = restore_backup(
                args.archive,
                database_url=settings.database_url,
                storage_root=settings.storage_root,
                replace=args.replace,
            )
            sys.stdout.write(f"restored: schema {manifest['schema_revision']}; run migrations if the code is newer\n")
    except BackupError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
