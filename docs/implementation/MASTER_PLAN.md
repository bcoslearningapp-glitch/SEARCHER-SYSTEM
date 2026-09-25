# Master Plan — Product B v1

Authority: `docs/product/RESEARCH_CORE_V1.md` > `docs/product/PRD_PRODUCT_B.md` > accepted ADRs > `CLAUDE.md`.

This plan decomposes the PRD (§76 phases, §83 first vertical slice) into work items with dependencies and exit criteria. GitHub Issues are the execution backlog; the work-item keys below (e.g. `P1-03`) are referenced in issue titles.

## Milestones

| Milestone | Tag | Scope | Exit criteria |
|---|---|---|---|
| M0 Foundation | v0.1.0 | Phase 0 | Clean clone starts locally; CI green; migration + rollback smoke; no product feature outside architecture |
| M1 Framing & Library | v0.2.0 | Phase 1 + first vertical slice (non-AI half) | Create -> frame -> approve flow; PDF upload with page anchors; metadata-only physical source; audited state changes |
| M2 Reference, Evidence, Hypothesis | v0.3.0 | Phase 2 | Reference review trace source -> interpretation -> inference -> judgment; exact quote protected; hypothesis supported/contradicted without losing history |
| M3 AI Research Engine | v0.4.0 | Phase 3 + vertical slice AI half | Same task on both providers; provider switch does not alter schema; no DB credentials to providers; counter-evidence track runs |
| M4 Design, Experiments, Memory | v0.5.0 | Phase 4 | Hypothesis -> design -> experiment -> learning workflow |
| M5 Outputs & Portability | v0.9.0 | Phase 5 | Export/import round trip preserves identity and trust; missing asset -> METADATA_ONLY; referenced output traces claims to source |
| M6 Hardening | v1.0.0 | Phase 6 | PRD §78 Definition of Done |

## Phase 0 — Foundation (M0)

| Key | Work item | PRD refs | Depends on | Status |
|---|---|---|---|---|
| P0-01 | Commit PRD, Research Core, CLAUDE.md, GitHub setup | §79.1 | — | Done |
| P0-02 | Repository layout, uv workspace, Makefile, .env.example | §57, §75 | P0-01 | Done |
| P0-03 | Research Core contracts package (enums, common, project, source identity, events, package manifest) + checker + generated bindings | §59 | P0-02 | Done |
| P0-04 | FastAPI skeleton: config, JSON logging with redaction, health/readiness, 14 bounded modules | §58, §68, §72 | P0-02 | Done |
| P0-05 | Alembic migrations; PostgreSQL + pgvector | §55, §60 | P0-04 | Done |
| P0-06 | Audit framework: append-only audit/research events, AI provenance enforcement | §40, §53, §67 | P0-05 | Done |
| P0-07 | Worker: Celery/Redis, durable job state machine, cancellation | §48, NFR-REL-002 | P0-05 | Done |
| P0-08 | Next.js shell: five research spaces, en/fr/ar with RTL, system status | §8, NFR-I18N-001 | P0-02 | Done |
| P0-09 | Docker images + docker compose single-command startup | §57 | P0-04..08 | Done |
| P0-10 | CI (ci, e2e, security, provider-contract, release) with required check names | §79.7-79.8 | P0-09 | Done |
| P0-11 | ADRs 001-005, architecture docs, quality-gates doc | §81 | — | Done |
| P0-12 | Protect `main` with required checks (repository settings; needs admin) | §79.6 | P0-10 | Waiting on repository admin |

## Phase 1 — Project, framing, source library (M1)

GitHub issues: #2 (P1-01/02), #3 (P1-03/04), #4 (P1-05/06/07), #5 (P1-08/09/11), #6 (P1-10), #7 (P1-12/13).

| Key | Work item | PRD refs | Depends on |
|---|---|---|---|
| P1-01 | Actor/identity model: local owner account, roles, actor on every request (role-aware, single-user OK). ADR for auth mechanism | §62, ADR required | P0-06 |
| P1-02 | Policy Engine v0: action authorization classes, deterministic transition rules, approval requirement evaluation (code/config, not prompts) | §49, FR-ACTION-001, FR-APPROVAL-001 | P1-01 |
| P1-03 | Project aggregate: create (FR-PROJ-001..003), lifecycle state machine (ProjectStatus ⟂ ResearchMode), fork with lineage (FR-PROJ-004), audit + ResearchEvents | §9-10 | P1-02 |
| P1-04 | Research State: persisted current question/mode/findings/unresolved/hypotheses/reservations/blockers/pending decisions/next action + reason | §38 FR-STATE-001/002 | P1-03 |
| P1-05 | Scratch space + research dialogue shell (notes never auto-promoted; explicit capture) | §39, FR-FRAME-001..003 | P1-03 |
| P1-06 | Problem Frame: versioned drafts, explicit approval action, SUPERSEDED on material change, Framing Gate v0 | FR-FRAME-004..007, §41 | P1-02, P1-04 |
| P1-07 | Decisions & approvals: Decision record (FR-DEC-001/002), explicit Approval entity, "Needs Your Attention" queue | §40, §65 | P1-02 |
| P1-08 | Storage abstraction: sandboxed filesystem object store (S3-compatible interface), upload validation, checksums. ADR for storage | SEC-006/007, §57 | P0-04 |
| P1-09 | Source identity: SourceWork/SourceEdition/SourceAsset, access modes, verification states, environment-specific availability | §15 FR-SRC-001..008 | P1-03, P1-08 |
| P1-10 | Ingestion pipeline v0: fingerprint, metadata, text extraction with page anchors, text-origin tagging, chunking (worker job). ADR for PDF/OCR stack | §17 FR-INGEST-001..004 | P1-09, P0-07 |
| P1-11 | Hybrid Source Access: SourceAccessRequest for known-but-unavailable sources; responses keep correct verification state; SOURCE_LEAD for researcher memory | §16, Core §26-27 | P1-09 |
| P1-12 | Library UI + Desk UI (project list/create, frame drafting/approval, attention queue, source catalog) with loading/error/empty states | §8 | P1-03..P1-11 |
| P1-13 | E2E: create -> frame -> approve; add digital source -> extract; add physical metadata-only source -> Hybrid Access | §73 E2E 1-3 | P1-12 |

## Phase 2 — Reference, claims, evidence, hypothesis (M2)

GitHub issues: #11 (P2-01), #12 (P2-02/03/04), #13 (P2-05/10), #14 (P2-06/09), #15 (P2-07/08), #16 (P2-11).

| Key | Work item | PRD refs |
|---|---|---|
| P2-01 | Claims & assumptions (types, epistemic category ⟂ workflow, AI-inferred labeling, criticality, note -> entity capture) | §12 |
| P2-02 | Foundational library isolation; constitutional authority approvals; hierarchy change audit | §18 |
| P2-03 | Qur'an structured source (approved dataset, checksum, exact text retrieval; no model regeneration) | §19 |
| P2-04 | Hadith record framework (edition-aware numbering, no merged narrations) | §20 |
| P2-05 | Reference review: 4-layer trace, judgment states, reservations, directness, interpretation divergence | §21 |
| P2-06 | Evidence model: roles, qualitative strength, assessment dimensions, lineage & independence detection | §26-27 |
| P2-07 | Hypothesis lab: lifecycle, immutable versions, epistemic downgrade, competing hypotheses | §13 |
| P2-08 | Mechanisms as first-class entities with links | §14 |
| P2-09 | Exact quotation protection (SourceExcerpt spans, verification, immutability) | Core §29, FR-INGEST-004 |
| P2-10 | Operational constraints (distinct from reference judgment) | §5.3 |
| P2-11 | Map & Lab UI; E2E 4-5 | §8, §73 |

## Phase 3 — Research engine and AI integration (M3)

AI gateway (AIProvider interface, Anthropic + OpenAI adapters, model profiles, disclosure records, redaction/context minimization, sensitivity policy), controlled tool registry, Research Orchestrator with structured proposals + validation before mutation, SearchProvider interface + web adapter, research plans with support/challenge/alternative tracks, search audit, sufficiency, cost tracking/budgets, provider-contract suite, AI reliability registry. Completes the vertical slice (PRD §83). E2E 9 (provider outage).

## Phase 4 — Design, experiments, memory (M4)

Design requirements/concepts/hypotheses with origins, experiments workflow, observation/result/interpretation separation, human-impact review, knowledge lifecycle & promotion gate, operating rules, temporal validity, transferability, terminology. E2E 6, 10.

## Phase 5 — Outputs, portability, cloud workspace (M5)

Output composer + 8-step integrity pipeline, multilingual integrity, citation/quote verification, Markdown/HTML (+DOCX/PDF) export, Research Core Package export/import with checksum validation and trust preservation, CloudWorkspaceAdapter (ADR for provider), disclosure manifest. E2E 7-8.

## Phase 6 — Hardening (M6)

Full E2E suite, security review, AI evaluation suite (`docs/evaluation/QUALITY_GATES.md` thresholds), performance benchmark, backup/restore docs, user docs, release artifacts.

## Open architecture decisions (ADR needed before the dependent work item)

| Decision | Needed by |
|---|---|
| ~~Authentication mechanism~~ — ADR-006 | P1-01 |
| ~~Storage abstraction~~ — ADR-007 | P1-08 |
| ~~PDF text extraction / OCR stack~~ — ADR-008 (OCR itself still open) | P1-10 |
| ~~Policy Engine implementation approach~~ — ADR-006 | P1-02 |
| Default multilingual embedding model (benchmarked) | Phase 3 retrieval |
| ~~Web search provider order~~ — ADR-012 (local library first, then provider-native web search) | Phase 3 |
| ~~Cloud workspace adapter~~ — ADR-023 (reference `local-directory` adapter; the concrete remote provider waits on the owner, #28) | Phase 5 |
| ~~PDF/DOCX renderer~~ — ADR-024 (python-docx; fpdf2 with HarfBuzz shaping; bundled Amiri fonts) | Phase 5 |
