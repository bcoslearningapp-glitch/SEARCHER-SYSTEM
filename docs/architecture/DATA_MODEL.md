# Data Model

Current schema (migrations `0001`–`0013`), by owning module:

| Migration | Tables | Integrity rules |
|---|---|---|
| 0001 platform, governance | `audit_events`, `research_events`, `background_jobs` | Events append-only (trigger); AI actor ⇒ `ai_action` |
| 0002 project workflow | `projects`, `research_states`, `scratch_notes`, `problem_frame_versions`, `approvals`, `quality_gate_evaluations`, `decisions`, `project_closures` | Approved frames immutable; approvals human-only |
| 0003–0004 sources | `source_works`, `source_editions`, `source_assets`, `project_sources`, `source_excerpts`, `source_access_requests`, `source_leads`, `source_pages`, `source_chunks` | Content-addressed assets; excerpts append-only; OCR never exact quote until verified |
| 0005–0006 claims, evidence, hypotheses | `claims`, `assumptions`, `open_questions`, `evidence`, `source_lineage`, `research_track_runs`, `hypotheses`, `hypothesis_versions`, `hypothesis_competitions`, `mechanisms`, `hypothesis_mechanisms` | Assessed evidence immutable; hypothesis versions append-only |
| 0007 reference, constraints | `foundational_sources`, `quran_surahs`, `quran_ayat`, `hadith_records`, `reference_reviews`, `reference_entries`, `reference_judgments`, `operational_constraints` | Foundational text and judgments append-only; human approval (ADR-009) |
| 0008 AI gateway | `project_ai_policies`, `ai_requests` | Request log append-only; written in its own transaction (ADR-010) |
| 0009 research planning | `research_plans`, `search_records`, `sufficiency_assessments`; web-origin columns on `source_leads` | Plan versions immutable except ACTIVE→SUPERSEDED; audit and sufficiency append-only (ADR-012) |
| 0010 AI tools | `ai_tool_calls` | Append-only; written in its own transaction (ADR-013) |
| 0011 AI reliability | `ai_evaluations` | Append-only; Methodology Steward or golden-evaluation system principal only (ADR-014) |
| 0012 design | `design_requirements`, `design_concepts`, `design_concept_coverage` | Requirement versions immutable except forward status moves; concepts never deleted; selection/rejection human-only approvals (ADR-015) |
| 0013 experiments | `design_hypotheses`, `design_hypothesis_versions`, `experiments`, `experiment_transitions`, `human_impact_assessments`, `experiment_observations`, `experiment_results`, `experiment_interpretations` | Versions, transitions, assessments, observations, results and interpretations append-only; hypotheses and experiments never deleted (ADR-016) |

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

Migration `0006` (Phase 2, issues #14/#15):

| Table | Purpose | Notes |
|---|---|---|
| `evidence` | Source-derived finding ↔ claim/hypothesis/mechanism with role and track | must reference a `source_excerpts` row; CHECK accepted ⇒ assessment; immutable once assessed (trigger) |
| `source_lineage` | Dependency between works | CITES/REPLICATES don't merge origins; DERIVED_FROM/USES_DATA_FROM/SUMMARIZES/REANALYZES/TRANSLATES do |
| `research_track_runs` | Support / challenge / alternative searches with bounded outcome and scope | failures never count as "searched" |
| `hypotheses` | Current pointer (lifecycle ⟂ epistemic state) | |
| `hypothesis_versions` | Immutable snapshots | append-only (trigger) |
| `mechanisms`, `hypothesis_mechanisms`, `hypothesis_competitions` | First-class mechanisms; links; competing hypotheses | |

Evidence aggregation rules live in `claims_evidence/aggregation.py` (pure, unit-tested): single origin caps at PROMISING; CONTESTED only for meaningful conflict; accepted evidence can downgrade a hypothesis automatically, upgrades need a human.

Migration `0007` (Phase 2, issues #12/#13, ADR-009):

| Table | Purpose | Notes |
|---|---|---|
| `foundational_sources` | Foundational library entries | STAGED → APPROVED → RETIRED; CHECK approved ⇒ human approver; one approved Qur'an text |
| `quran_surahs`, `quran_ayat` | Imported approved Qur'an dataset | byte-exact text; append-only |
| `hadith_records` | One narration per row | unique per (source, numbering scheme, number); append-only |
| `reference_reviews` | Review of a target under an analytical category | |
| `reference_entries` | Source text / approved interpretation / system synthesis / practical judgment | append-only; CHECK AI ⇒ SYSTEM_SYNTHESIS; CHECK source text is sourced |
| `reference_judgments` | Human judgments with directness, reservations, divergence | append-only; CHECK human judge; CHECK reservation iff RESERVED |
| `operational_constraints` | Law/regulation/contract/license/policy constraints | separate from reference judgments; resolvable |
