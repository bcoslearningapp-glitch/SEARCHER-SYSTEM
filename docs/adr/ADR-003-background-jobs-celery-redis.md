# ADR-003: Background execution with Celery on Redis; durable job state in PostgreSQL
Status: Accepted
Date: 2026-09-24

Context:
PRD §55/§57 recommend Redis and Celery (or an ADR-approved equivalent). NFR-REL-002 requires durable job status; FR-ORCH-004/005 require cancellable tasks whose status survives the browser session; NFR-REL-003 forbids partial mutation on failure.

Decision:
- Celery 5 with Redis as broker. Results backend disabled: the broker carries only a job ID.
- Job state lives in the `background_jobs` table (`research_api.platform.jobs`) with an explicit state machine: QUEUED -> RUNNING -> SUCCEEDED | FAILED | CANCELLED. Illegal transitions raise.
- Failures record a `failure_kind` (DISPATCH_FAILURE, APPLICATION_ERROR, PROVIDER_ERROR, STOPPED_RESOURCE_CONSTRAINT) so application, provider and resource failures stay distinguishable (PRD §72, FR-COST-003).
- `research_worker.runner.run_job` executes a job body in its own transaction; on exception the body's writes roll back and the job is marked FAILED.
- Cancellation: QUEUED jobs cancel immediately; RUNNING jobs get `cancel_requested` and must stop cooperatively.
- `task_acks_late` + `task_reject_on_worker_lost` so a crashed worker's task is redelivered; the runner skips jobs no longer QUEUED, making redelivery idempotent.

Alternatives considered:
- arq/RQ/Dramatiq: viable, but Celery is the PRD default and well understood.
- Postgres-only queue (e.g. SKIP LOCKED polling): fewer moving parts, but the PRD already requires Redis; revisit if Redis becomes a burden.

Consequences:
- Redis outage degrades background work (readiness reports `degraded`) but does not block reading/editing canonical data.

Research Core impact: Supports "search failure is not evidence absence" (Core §72) by keeping failure kinds explicit.

Migration impact: Adds `background_jobs` (migration 0001).
