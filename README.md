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

## Adopt the Qur'an text (Constitutional Authority)

The product ships with no Qur'anic text and never generates it (ADR-009). To adopt a published dataset, for example the King Fahd Glorious Qur'an Printing Complex (KFGQPC) Warsh narration:

1. Get the publisher's file: `git clone https://github.com/thetruetruth/quran-data-kfgqpc.git`, then use `quran-data-kfgqpc/warsh/data/warshData_v10.json`. That repository is a mirror of the KFGQPC developer data (https://qurancomplex.gov.sa/en/techquran/dev/), so compare the SHA-256 the app shows with the file from KFGQPC if you need that assurance.
2. In the app, open **Library → Foundational library (Qur'an text)**. Under **Import a Qur'an text dataset**, set the edition (e.g. `KFGQPC Uthmanic Warsh v10 (2021-08-05)`), choose the JSON file, and import. The text is **staged**; nothing is served yet.
3. Check the staged entry: 114 surahs, 6214 ayat for Warsh, the format `kfgqpc-json`, and its SHA-256 (`f05d0dc6…3872f` for `warshData_v10.json`).
4. Enter a reason and **Approve**. From then on, every exact Qur'an quotation in the product comes from this text. Approving another dataset later retires this one.
5. Optional, for publisher-faithful display: copy the KFGQPC font for the same narration (e.g. `warsh/font/warsh.10.woff2`) to `apps/web/public/fonts/quran/quran.woff2` and rebuild the web app. It is not committed, so check its licence yourself. Without it, the bundled Amiri Quran font (OFL) is used.

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

`docker compose exec api python -m research_api.ops.backup create --out /data/backups` writes one checksummed archive holding the database and every stored source file. Restoring, verifying and the guarantees are covered in [`docs/operations/BACKUP_RESTORE.md`](docs/operations/BACKUP_RESTORE.md).

## Contributing

See [`CLAUDE.md`](CLAUDE.md) and [`GITHUB_SETUP.md`](GITHUB_SETUP.md): Conventional Commits, one issue per PR, all required checks green, ADRs for durable decisions. Never commit secrets.
