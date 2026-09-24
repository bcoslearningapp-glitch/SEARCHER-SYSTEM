# Data Model

Current schema (migration `0001`):

| Table | Purpose | Notes |
|---|---|---|
| `audit_events` | Who did what to which entity, previous/new state, reason, AI provenance | Append-only trigger; CHECK: AI actor ⇒ `ai_action` present |
| `research_events` | Meaningful research changes (`ProblemFrameApproved`, ...) | Append-only trigger |
| `background_jobs` | Durable job state machine | QUEUED → RUNNING → SUCCEEDED/FAILED/CANCELLED |

Conventions:
- Primary keys are UUIDs (portable IDs, PRD §60.6).
- Every event stamps `core_schema_version`, `methodology_version`, `constitution_version`.
- Timestamps are `timestamptz`, stored in UTC.
- Constraint names follow the naming convention in `research_api/platform/db.py`.
- Epistemically meaningful entities will prefer archival over deletion (PRD §60.7); approved major versions are immutable rows (Problem Frame, Hypothesis versions).

The Research Core entity list (Core §15) will be added module by module per the Master Plan; the canonical shapes live in `packages/research-core-contracts`.

Migration `0002` (Phase 1, issues #3/#4):

| Table | Purpose | Notes |
|---|---|---|
| `projects` | Project aggregate | status ⟂ research_mode; version stamps; `forked_from_project_id` lineage |
| `research_states` | Durable Research State (1:1 project) | pending decisions computed from `decisions` |
| `project_closures` | Closure records | kept on reopen (`reopened_at`, `reopen_trigger`) |
| `scratch_notes` | Free-thinking notes | only explicit capture changes formal state |
| `problem_frame_versions` | Versioned Problem Frames | one DRAFT and one APPROVED per project (partial unique indexes); approved/superseded rows immutable (trigger) |
| `approvals` | Explicit human approvals | append-only; CHECK approver is HUMAN |
| `quality_gate_evaluations` | Gate results with findings | append-only |
| `decisions` | Decisions with AI recommendation kept separate | CHECK: DECIDED ⇒ human + decision + justification; immutable once resolved (trigger) |

Migrations `0003`/`0004` (Phase 1, issues #5/#6):

| Table | Purpose | Notes |
|---|---|---|
| `source_works` | The intellectual work (library-wide) | `authority_layer`; foundational layers need Constitutional Authority |
| `source_editions` | Specific edition/translation | starts `METADATA_ONLY`; changes only via audited reverification |
| `source_assets` | Concrete file or holding | environment-specific `available_in_environment`; sha256 + storage key; ingestion status/job |
| `project_sources` | Works used by a project | |
| `source_excerpts` | Located content (e.g. access responses) | append-only; CHECK: OCR text cannot be an exact quote unless verified |
| `source_access_requests` | Hybrid Source Access requests | OPEN → PARTIALLY_FULFILLED/FULFILLED/CANCELLED |
| `source_leads` | Researcher memory of a source | CHECK: VERIFIED ⇒ linked excerpt |
| `source_pages` / `source_chunks` | Derived page text and retrieval chunks | `tsv` generated column + GIN index |

Migration `0005` (Phase 2, issue #11):

| Table | Purpose | Notes |
|---|---|---|
| `claims` | Claims with type, statement origin, workflow state ⟂ epistemic strength | new claims are `UNSUBSTANTIATED`; AI claims enter `PROPOSED` |
| `assumptions` | Explicit / system-inferred / source-derived assumptions with criticality | CHECK: SYSTEM_INFERRED ⇒ AI_GENERATED provenance; human review confirms/rejects/reclassifies |
| `open_questions` | Explicit research questions | closing may conclude `INSUFFICIENT_EVIDENCE` ("unknown" is valid) |
