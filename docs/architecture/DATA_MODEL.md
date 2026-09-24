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
