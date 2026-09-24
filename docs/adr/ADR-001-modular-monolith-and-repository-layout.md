# ADR-001: Modular monolith, uv workspace, and repository layout
Status: Accepted
Date: 2026-09-24

Context:
PRD §57-58 and CLAUDE.md require a v1 modular monolith with bounded domain modules, a FastAPI backend, a separate background worker, a Next.js frontend, and a provider-neutral contracts package. The API and worker must share domain code without duplicating it or letting modules bypass each other.

Decision:
- One Python package, `research_api` (services/api), holds all domain modules under `research_api/modules/<module>` (the 14 modules of PRD §58) plus cross-cutting infrastructure under `research_api/platform`.
- The worker (`research_worker`, services/worker) is a thin package that depends on `research_api` and registers tasks; it owns no domain rules.
- Both are members of a single uv workspace at the repository root with one lockfile (`uv.lock`) and one backend Docker image used for `api`, `worker` and `migrate`.
- Each module's public surface is its `service` module. Importing another module's `models` is forbidden and enforced by `tests/unit/test_architecture.py`, which also forbids provider SDK imports outside `ai_gateway`.
- Layout follows PRD §75: `apps/web`, `services/api`, `services/worker`, `packages/research-core-contracts`, `docs/*`, `infra/docker`, `tests/e2e`, `scripts`.

Alternatives considered:
- Separate API and worker codebases: duplicates domain logic; rejected.
- Microservices: out of scope for v1 (PRD §57).
- Poetry/pip-tools: uv gives a fast, reproducible workspace lock across both packages.

Consequences:
- One migration history and one ORM metadata for the whole system.
- Boundary discipline relies on code review plus the architecture tests; tests should grow as modules gain services.

Research Core impact: None directly; boundaries protect Core semantics from convenience shortcuts.

Migration impact: None.
