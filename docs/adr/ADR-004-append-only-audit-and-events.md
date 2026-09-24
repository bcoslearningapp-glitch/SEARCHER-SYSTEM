# ADR-004: Append-only audit and research events, enforced in the database
Status: Accepted
Date: 2026-09-24

Context:
PRD §40 and §67 require auditable events for material state changes, identifying actor, entity, previous/new state, methodology/constitution versions and AI provenance. PRD §60 says audit is append-oriented and v1 need not use full event sourcing. Core §56 requires Event and Action to stay distinct.

Decision:
- Two tables: `audit_events` (who did what, with previous/new state and reason) and `research_events` (meaningful research changes such as `ProblemFrameApproved`).
- Both are append-only: a PL/pgSQL trigger rejects UPDATE, DELETE and TRUNCATE. History cannot be rewritten through the application or ad-hoc SQL by the app role.
- Every record stamps `core_schema_version`, `methodology_version`, `constitution_version` and actor kind/id/role.
- AI-actor audit records must carry `ai_action` provenance (provider, model, template version, supplied entity IDs, timestamp). Enforced by Pydantic, by a DB CHECK constraint, and by the contract schema.
- Domain services call `governance_audit.service.record_audit` / `record_research_event` inside their own transaction so the audit record commits or rolls back atomically with the change it describes.
- The audit HTTP API is read-only.
- Canonical state is stored in normal tables; events are not replayed to rebuild state (no full event sourcing in v1).

Alternatives considered:
- Full event sourcing: more complex than v1 needs (PRD §60.4).
- Application-level immutability only: bypassable; rejected.

Consequences:
- Corrections are new events, never edits. Test isolation uses rolled-back transactions rather than cleanup deletes.
- Retention/archival of audit data will need a documented, authorized procedure (SEC-009) rather than DELETE.

Research Core impact: Implements "does not silently rewrite research history" (PRD §87) and AI provenance (Core §71).

Migration impact: Migration 0001 creates the tables, trigger function and triggers; downgrade drops them.
