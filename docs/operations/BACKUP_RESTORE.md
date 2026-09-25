# Backup and restore

A backup captures the **whole installation**: the database, including every project, audit history, approvals and settings, together with every stored source file. It is one `.tar` archive with a checksummed manifest. The tool is `research_api.ops.backup` (#58).

To move a single project to another installation, use the Research Core Package instead: *Export package* on the project, *Import* on the home page (ADR-022).

## What is in an archive

| Entry | Content |
|---|---|
| `database.dump` | `pg_dump` custom-format dump (compressed) |
| `storage/…` | every file under the storage root: source assets, pages, derived text |
| `manifest.json` | format version, creation time, app version, schema revision, and the SHA-256 and size of every entry |

Remote cloud-workspace copies are not included. Their disclosure manifest is in the database (ADR-023).

## With Docker Compose

Backups are written to the `backups` volume, mounted at `/data/backups` in the API container.

```bash
# create
docker compose exec api python -m research_api.ops.backup create --out /data/backups
# list, and copy one to the host
docker compose exec api ls /data/backups
docker compose cp api:/data/backups/product-b-backup-20260925T120000Z.tar .
# verify every checksum without restoring
docker compose exec api python -m research_api.ops.backup verify /data/backups/product-b-backup-20260925T120000Z.tar
```

### Restore

1. Copy the archive into the volume, if it is not already there:
   ```bash
   docker compose cp product-b-backup-….tar api:/data/backups/
   ```
2. Stop the worker so no job writes during the restore:
   ```bash
   docker compose stop worker
   ```
3. Restore:
   ```bash
   docker compose exec api python -m research_api.ops.backup restore /data/backups/product-b-backup-….tar
   ```
   Restoring over an installation that already holds data replaces it, and refuses to run unless you add `--replace` (SEC-009). The whole archive is verified before anything is written.
4. If the code is newer than the backup, apply migrations, then restart:
   ```bash
   docker compose run --rm migrate
   docker compose up -d
   ```

## Without Docker

Any machine with PostgreSQL **16** client tools (`pg_dump`, `pg_restore`) and the installation's settings (`DATABASE_URL`, `STORAGE_ROOT`) can run the same commands:

```bash
cd services/api
uv run python -m research_api.ops.backup create --out ../../backups
```

The client major version must match the server. A newer `pg_dump` writes settings that a PostgreSQL 16 server rejects on restore.

## Guarantees and limits

- **Tested.** Ids, audit history and file checksums are identical after restoring into an empty database and storage root (`services/api/tests/integration/test_backup.py`).
- **Verified before writing.** A tampered or unsafe archive is refused before anything is written: a checksum mismatch, an unlisted entry, a path escaping the storage root, or a non-regular file.
- **Database first, then files.** The database restore is one transaction. Files are written after it; if writing files fails, re-running the restore with `--replace` completes it.
- **Secrets are not included.** Backups contain no secrets from the environment, but they do contain all research data. Store them like the original.
