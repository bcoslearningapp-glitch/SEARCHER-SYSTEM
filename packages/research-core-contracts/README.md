# research-core-contracts

Language-neutral, provider-neutral canonical contracts for Research Core v1.0 (ADR-002). Shared by Product A, B and C.

- `manifest.json` — `research_core_version` and `schema_version`
- `schema/enums.schema.json` — every normative Core enumeration, with section references
- `schema/common.schema.json` — IDs, timestamps, actor, provenance, AI action record, version context
- `schema/project.schema.json`, `schema/source-identity.schema.json`, `schema/event.schema.json`, `schema/package-manifest.schema.json`
- `examples/valid/<target>/` and `examples/invalid/<target>/` — `<target>` is `<schema stem>` or `<schema stem>.<$defs name>`

Validate: `uv run python scripts/contracts/check_contracts.py`
Regenerate bindings: `uv run python scripts/contracts/generate_bindings.py`

Rules: no AI-provider vocabulary; semantic changes follow Core §76 versioning; generated bindings are never edited by hand.
