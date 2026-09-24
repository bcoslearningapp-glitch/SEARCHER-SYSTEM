# Product B — Integrated AI Research System

A local-first research operating system that integrates cloud AI through provider adapters while keeping the canonical research project, sources, evidence, judgments, approvals and audit trail under local control.

> The governing reference framework governs; the researcher leads; the AI assists, expands, organizes, challenges, and tests.

- Product requirements: [`docs/product/PRD_PRODUCT_B.md`](docs/product/PRD_PRODUCT_B.md)
- Research Core v1.0 (normative): [`docs/product/RESEARCH_CORE_V1.md`](docs/product/RESEARCH_CORE_V1.md)
- Plan and status: [`docs/implementation/MASTER_PLAN.md`](docs/implementation/MASTER_PLAN.md), [`docs/implementation/STATUS.md`](docs/implementation/STATUS.md)
- Architecture: [`docs/architecture/OVERVIEW.md`](docs/architecture/OVERVIEW.md) and [`docs/adr/`](docs/adr/)

**Current state:** Phase 1 (M1): projects, Research State, Problem Frames with explicit approval, decisions, source library with Hybrid Source Access, PDF ingestion and search, in English, French and Arabic. See [`STATUS.md`](docs/implementation/STATUS.md).

## Prerequisites

- Docker with Docker Compose v2
- For development outside containers: [uv](https://docs.astral.sh/uv/) (Python 3.12 is fetched automatically) and Node.js 22

## Run locally

```bash
cp .env.example .env        # optional: add ANTHROPIC_API_KEY / OPENAI_API_KEY
docker compose up --build --detach --wait
```

- Web UI: http://localhost:3000 (English), `/fr` (French), `/ar` (Arabic, right-to-left)
- API: http://localhost:8000 — docs at http://localhost:8000/docs, readiness at `/health/ready`

Migrations run automatically (`migrate` service) before the API and worker start. Cloud AI keys are optional: the product stays usable without them.

Stop with `docker compose down` (data volumes are kept; add `--volumes` to erase local data).

## Develop

```bash
make setup          # uv sync + npm ci
make check          # contracts, lint, typecheck, unit tests
make up             # full stack
DATABASE_URL=postgresql+psycopg://research:research@localhost:5432/research make test-integration
make e2e            # Playwright smoke tests against the running stack
```

Research Core contracts live in `packages/research-core-contracts` (JSON Schema). After changing them run `make generate` — the Python and TypeScript enum bindings are generated, never hand-edited.

## Repository layout

| Path | Purpose |
|---|---|
| `apps/web` | Next.js frontend (Desk, Map, Library, Lab, Outputs) |
| `services/api` | FastAPI backend: `research_api/modules/*` bounded domain modules, `platform/*` infrastructure, Alembic migrations |
| `services/worker` | Celery worker for long-running tasks |
| `packages/research-core-contracts` | Provider-neutral canonical contracts |
| `scripts/contracts` | Contract validation and binding generation |
| `infra/docker` | Dockerfiles |
| `tests/e2e` | Cross-stack Playwright tests |
| `docs/` | Product, architecture, ADRs, plan/status, evaluation |

## Backup and restore (local)

```bash
docker compose exec -T postgres pg_dump -U research -Fc research > backup.dump
docker compose exec -T postgres pg_restore -U research -d research --clean < backup.dump
```

Source assets are stored in the `source-storage` Docker volume.

## Contributing

See [`CLAUDE.md`](CLAUDE.md) and [`GITHUB_SETUP.md`](GITHUB_SETUP.md): Conventional Commits, one issue per PR, all required checks green, ADRs for durable decisions. Never commit secrets.
