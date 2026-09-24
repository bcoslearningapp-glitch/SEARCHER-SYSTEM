# Security

Implemented in the foundation:
- Secrets only via environment/`.env` (gitignored); `.env.example` has placeholders only (SEC-001).
- Provider keys are `SecretStr`; never in reprs (SEC-003).
- JSON logs recursively redact secret-looking keys and values (API keys, bearer tokens, URL credentials) (SEC-003).
- Browser never receives API URLs or secrets: the web app calls the API server-side (`server-only`) (SEC-002).
- Audit/research event tables are append-only at the database level (PRD §60).
- Containers run as non-root; compose publishes ports on 127.0.0.1 only.
- CI: gitleaks secret scan, pip-audit, npm audit, Ruff bandit rules.

Planned (see Master Plan): upload validation and sandboxed storage paths (SEC-006/007, P1-08), tool permission enforcement server-side (FR-AI-TOOL-004), prompt-injection handling of untrusted source text (PRD §51), disclosure records for outbound AI requests (FR-DATA-001), package checksum validation on import (SEC-010).
