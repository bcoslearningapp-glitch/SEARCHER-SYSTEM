# Portability (planned — Phase 5)

The Research Core Package manifest contract exists already: `packages/research-core-contracts/schema/package-manifest.schema.json`.

- Entries carry SHA-256 checksums; paths are relative and traversal-free (SEC-010).
- Excluded assets are listed with a reason; on import their sources become `METADATA_ONLY` rather than disappearing (FR-PORT-004).
- Import never raises `SourceVerificationState`; only an explicit ReverificationEvent may (FR-SRC-007/008).
- Every entity keeps its UUID across products.
