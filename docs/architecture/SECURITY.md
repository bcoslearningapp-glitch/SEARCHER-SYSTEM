# Security

The M6 security review is #55. This document is the threat model, the control for each PRD §68 requirement, and the residual risks that remain.

## Threat model

Product B is a local-first, single-owner installation (ADR-006). The web app (port 3000) calls the API (port 8000) server-side. The worker, Postgres and Redis sit behind them. In compose, every port is published on 127.0.0.1 only.

| Actor | Can reach | Main risks |
|---|---|---|
| Web pages open in the researcher's browser | `localhost:3000` and `localhost:8000` through the browser | cross-site request forgery (CSRF), DNS rebinding that reads research data |
| Source content: PDFs, text, web results, datasets | ingestion, retrieval, AI prompts | prompt injection, parser bugs, oversized files |
| AI providers | only the content the gateway sends | exceeding the disclosure policy, unauthorised tool use, fabricated evidence |
| Imported packages and Qur'an datasets | the import paths | path traversal, checksum mismatch, trust escalation, zip bombs |
| Cloud workspace | payload bytes chosen by a person | credential leakage, silent synchronisation |
| Other local users or processes on the machine | the local ports | out of scope for single-owner mode, which the host OS account protects (ADR-006) |

## Controls (PRD §68)

| Requirement | Control | Verified by |
|---|---|---|
| SEC-001 No keys in git | Secrets only via environment or `.env` (gitignored); gitleaks in CI | `secret-scan` job |
| SEC-002 No secrets in browser bundles | The web app calls the API server-side (`server-only`); the browser never receives API URLs or keys | `lib/api.ts` imports `server-only` |
| SEC-003 Log redaction | Keys are `SecretStr`. JSON logs recursively redact secret-looking keys and values. Outbound prompts redact credentials from connection strings. | `unit/test_logging.py`, `integration/test_m3_exit.py` |
| SEC-004 No DB credentials for AI | No SQL, file or shell tools; closed tool schemas; the cloud workspace refuses payloads that contain the database URL, its credentials, the Redis URL or provider keys | `unit/test_ai_tool_registry.py`, `integration/test_cloud_workspace.py` |
| SEC-005 No model-generated SQL | Model output is schema-validated data, never executed; all queries are ORM-built | `unit/test_architecture.py`, review (no `text()` built from model output) |
| SEC-006 Upload validation | Size caps; the media type is sniffed from bytes against an allow-list; the client's declared type is ignored | `unit/test_storage.py`, `integration/test_sources.py` |
| SEC-007 Sandboxed paths | Content-addressed storage under the configured root; resolved-path checks; workspace keys limited to `[A-Za-z0-9-]` | `unit/test_storage.py`, `unit/test_adapter_contracts.py` |
| SEC-008 Source text is untrusted | Untrusted sections are fenced in prompts, and injection-resistance golden fixtures cover them; staged workspace payloads are labelled "data, never instructions" | `unit/test_golden.py`, `integration/test_ai_gateway.py` |
| SEC-009 Destructive administration | No delete endpoints for research records. A database trigger keeps records (`keep_research_record`). Removing a staging deletes only the remote copy and keeps the manifest. Export, import and staging are human-only policy actions. | `unit/test_policy.py`, trigger tests |
| SEC-010 Package validation | Manifest contract, per-entry SHA-256, safe paths, no unlisted files, size caps, schema-revision check, all inside one savepoint | `integration/test_portability.py` |
| SEC-011 Least privilege | Policy Engine denies unregistered actions; per-task tool allow-lists; approvals are human-only; a project's disclosure policy gates every outbound call | `unit/test_policy.py`, `integration/test_ai_tools.py` |

### HTTP boundary (#55)

**API** (`platform/security.py`):
- **Host allow-list** (`ALLOWED_HOSTS`). This defeats DNS rebinding, where an attacker's domain resolves to 127.0.0.1.
- **Cross-site write refusal.** A request with an unsafe method is refused when:
  - it carries an `Origin` that is not in `CORS_ORIGINS`; or
  - it carries `Sec-Fetch-Site: cross-site`.
  This is needed because multipart uploads and body-less POSTs are "simple" requests that skip the CORS preflight.
- **Response headers on every response:** `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and a `default-src 'none'; sandbox` CSP.

**Web** (`src/proxy.ts`, `next.config.ts`):
- **Host allow-list** (`WEB_ALLOWED_HOSTS`).
- **Security headers:** framing denied, `nosniff`, a Permissions-Policy, and a CSP limited to `frame-ancestors` / `object-src` / `base-uri`.
- **Server actions:** Next.js checks the request's `Origin` against its `Host` itself.

**Containers:** non-root users; ports published on 127.0.0.1 only.

### Dependency hygiene

CI runs:
- pip-audit and npm audit;
- Ruff's bandit rules;
- gitleaks.

New dependencies and their licences are recorded in ADRs (for example ADR-024).

## Residual risks

- **No per-user authentication.** Single-owner mode trusts anyone who can reach the local ports. Multi-user deployment needs the authentication ADR follow-up (ADR-006).
- **No strict script CSP on the web app.** Next's inline runtime would need nonces. The app renders no untrusted HTML: React escapes output, and exported HTML is a download (`attachment`).
- **Untrusted PDFs are parsed** by pypdf in the worker. A crafted file can cost CPU or memory in that job, but it cannot reach the API process.
- **Cloud workspace orphans.** A remote copy written just before a database rollback has no manifest row (ADR-023).
- **Prompt injection** is reduced by fencing untrusted text, closed tool schemas and human approval of every canonical change, but no model is immune. Evaluation thresholds are tracked in `docs/evaluation/QUALITY_GATES.md`.
