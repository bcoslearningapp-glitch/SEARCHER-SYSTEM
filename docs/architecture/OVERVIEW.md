# Architecture Overview

Product B is a local-first modular monolith (ADR-001).

```
Browser ──> web (Next.js, server-side API calls only)
               │
               ▼
            api (FastAPI) ──────────────┐
               │   ▲                    │ enqueue job id
               │   │ read/write         ▼
               ▼   │                  redis ──> worker (Celery)
          PostgreSQL + pgvector  <──────────────────┘
          (canonical state, audit, job status)
```

- **Canonical state** lives only in local PostgreSQL. Cloud AI providers (Phase 3) are reached through `modules/ai_gateway` adapters and never receive database credentials (FR-AI-TOOL-001).
- **Domain modules** (`services/api/research_api/modules/`) follow PRD §58. Public surface = each module's `service`. Architecture tests forbid cross-module `models` imports and provider SDK imports outside `ai_gateway`.
- **Platform** (`research_api/platform/`): config, DB, JSON logging with secret redaction, health, durable background jobs, queue dispatch.
- **Contracts** (`packages/research-core-contracts`): JSON Schema source of truth; bindings generated for Python and TypeScript (ADR-002).
- **Audit** (`modules/governance_audit`): append-only `audit_events` and `research_events`, enforced by DB triggers (ADR-004).
- **Jobs**: job state machine in PostgreSQL; broker carries only job IDs (ADR-003).
- **Readiness** depends on PostgreSQL (required) and Redis (degraded if down); missing/unavailable AI providers never make the product unready (NFR-REL-001).

See also: [DATA_MODEL.md](DATA_MODEL.md), [SECURITY.md](SECURITY.md), [AI_ORCHESTRATION.md](AI_ORCHESTRATION.md), [PORTABILITY.md](PORTABILITY.md).
