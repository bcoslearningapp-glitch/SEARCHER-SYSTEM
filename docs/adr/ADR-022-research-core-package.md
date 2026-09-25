# ADR-022: Research Core Package export and import
Status: Accepted
Date: 2026-09-24

Context:
PRD §45 (FR-PORT-001..006), Core §68-69 and SEC-010 require:
- a versioned package that preserves project and entity identities, source metadata, relationships, versions, provenance, verification, decisions, audit and version context;
- assets that are optional and governed by portability and licence;
- missing assets become metadata-only, and are never deleted;
- import validates schema compatibility;
- trust never upgrades on import.

Decision:
- **Format.** A zip file holding:
  - `manifest.json`, which follows the existing `package-manifest` contract and adds `schema_revision` and `counts`;
  - `entities/<table>.jsonl`, rows with their original portable UUIDs, where audit tables are marked `audit`;
  - `assets/<sha256>`.
  Every entry is checksummed in the manifest.
- **What is exported.** Rows are collected generically from the ORM metadata, in dependency order:
  - every table carrying the project's `project_id`, then their child rows through foreign keys;
  - the library records the project uses: works, editions, assets, cited excerpts, lineage between included works, referenced Hadith records and their foundational source;
  - no `background_jobs`, which are operational.
  - `knowledge_reuses` link two projects, so they are left out of a single-project package.
  - Computed columns such as the search tsvector are rebuilt by the database.
- **Asset bytes** travel only when the edition allows portability (`portable_asset_allowed`). Page text and search chunks are derived from the file, so they travel only with its bytes. Withheld files are listed in `excluded_assets` with the reason.
- **Import** runs inside a savepoint, and nothing is written until every check passes:
  - the zip is readable and within size limits;
  - the manifest is valid against its contract;
  - every listed entry exists, has a safe path, and matches its SHA-256, and no unlisted files are present;
  - the package's `schema_revision` is not newer than this installation's;
  - only known tables and columns appear;
  - the project does not already exist here. A package never overwrites a project.
  A database error during insert rolls everything back and is reported as incompatible.
- **Trust never upgrades** (FR-PORT-006):
  - Shared library rows use `ON CONFLICT DO NOTHING`, so an existing row here stays exactly as it is.
  - Foundational sources arrive STAGED with no approver; the local Constitutional Authority decides.
  - An asset is `available_in_environment` only if its bytes arrived intact and were stored. Otherwise it keeps its metadata and relationships and is metadata-only (FR-PORT-004).
  - A fork link to a project that is absent here is cleared.
- **Human-only actions.** Export and import are human-only policy actions, and both are audited. The import also records a `ProjectImported` event carrying the trust notes.

Consequences:
- Contracts 0.13.0 add `schema_revision` and `counts` to the manifest.
- The round trip is tested against a second, freshly migrated database.
- A later "import as copy" (new ids) could allow importing into an environment where the project already exists. It is not needed for v1.
