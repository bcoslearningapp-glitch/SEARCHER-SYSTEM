# ADR-005: Initial stack and version pins
Status: Accepted
Date: 2026-09-24

Context:
PRD §57 and §85 leave exact versions to implementation; they must be current, stable and pinned in lockfiles.

Decision:
- Python 3.12 (runtime image `python:3.12-slim`), FastAPI, Pydantic 2, SQLAlchemy 2 (sync, psycopg 3), Alembic. Locked in `uv.lock`.
- PostgreSQL 16 with pgvector (`pgvector/pgvector:pg16`), Redis 7.
- Node 22 LTS; Next.js 16 (App Router, standalone output), React 19, Tailwind CSS 4, Vitest. Exact versions in `apps/web/package.json` + `package-lock.json`.
- TypeScript 5.9 and ESLint 9 rather than TypeScript 7 / ESLint 10: the Next.js/typescript-eslint plugin ecosystem support for the newer majors is not yet established. Revisit once `eslint-config-next` declares support.
- UI localization: route-level locales `en`, `fr`, `ar` with `dir="rtl"` for Arabic (NFR-I18N-001), implemented without an i18n library until needs outgrow simple dictionaries.
- E2E: Playwright against the docker compose stack.

Alternatives considered:
- Async SQLAlchemy: adds complexity with little benefit at local-workstation scale; can be revisited per module.

Consequences:
- Dependency updates go through PRs with the full check suite.

Research Core impact: None.

Migration impact: None.
