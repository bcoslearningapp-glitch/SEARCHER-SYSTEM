# Status

**Current milestone:** M0 Foundation (v0.1.0) — implementation complete, awaiting CI on GitHub and `main` protection.

## Completed
- P0-01..P0-11: docs committed; uv workspace; Research Core contracts package + checker + generated Python/TS bindings; FastAPI skeleton with JSON logging/redaction and health/readiness; Alembic + pgvector; append-only audit/research events; Celery worker with durable job state; Next.js shell (5 spaces, en/fr/ar, RTL); Docker Compose stack; CI/E2E/security/provider-contract/release workflows; ADR-001..005.
- Verified locally: backend lint/format/mypy, 39 API tests (unit + integration), 4 worker tests, 7 frontend tests, frontend lint/typecheck/build, contract check, migration up/down/up + `alembic check`, `docker compose up` with all services healthy, 5 Playwright E2E smoke tests, pip-audit and npm audit clean, actionlint clean.

## In progress
- Nothing.

## Blocked
- P0-12 `main` branch protection: the repository has no `main` branch yet; work is on `claude/go-on-6o01fg`. Protection requires repository admin settings.

## Next
- Merge the foundation into `main`, then protect `main` with the required checks listed in GITHUB_SETUP §13.
- Phase 1, starting with P1-01 (actor/auth ADR), P1-02 (Policy Engine v0), P1-03 (Project aggregate).
