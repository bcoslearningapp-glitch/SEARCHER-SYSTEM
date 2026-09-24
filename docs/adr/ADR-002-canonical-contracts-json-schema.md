# ADR-002: JSON Schema as the canonical Research Core contract with generated bindings
Status: Accepted
Date: 2026-09-24

Context:
PRD §59 requires product-independent, versioned, language-neutral Research Core contracts free of AI-provider structures. Products A, B and C must share them. The Python backend and TypeScript frontend both need the enumerations, and drift between them would silently change Core semantics.

Decision:
- `packages/research-core-contracts/schema/*.schema.json` (JSON Schema draft 2020-12) is the single source of truth. `manifest.json` declares `research_core_version` and `schema_version`.
- `enums.schema.json` holds every normative Core enumeration as a `$defs` entry with section references.
- `scripts/contracts/generate_bindings.py` generates `services/api/research_api/contracts/enums.py` (StrEnum) and `apps/web/src/lib/contracts/enums.ts` (const arrays + union types). Generated files are never hand-edited.
- `scripts/contracts/check_contracts.py` validates schemas, runs positive and negative examples, enforces enum hygiene, and rejects provider-specific vocabulary. CI job `contract-check` runs it and verifies bindings are fresh.
- Backend responses that correspond to contract entities are validated against the schemas in tests (e.g. audit events).

Alternatives considered:
- Pydantic models as the source with exported JSON Schema: couples the portable contract to one language and product.
- Protobuf/Avro: weaker fit for document-style portable packages and human review.

Consequences:
- Contract changes are explicit diffs to schema files, reviewable as product changes.
- Schema versioning follows Core §76 (patch/minor/major).

Research Core impact: Encodes Core vocabulary exactly; any Core change must start here.

Migration impact: Schema major versions will require portability migrations (FR-PORT-005).
