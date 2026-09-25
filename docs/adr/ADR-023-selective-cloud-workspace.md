# ADR-023: Selective cloud workspace and disclosure manifest
Status: Accepted
Date: 2026-09-25

Context:
PRD §56 (FR-CLOUD-001..007) asks for an optional selective cloud workspace:
- nothing is ever synchronised silently;
- a person selects what is staged, and the selection is policy-checked;
- a disclosure manifest records what was staged;
- the remote side exposes controlled tools, never database credentials;
- the local database stays canonical;
- remote content can expire and be deleted;
- the provider sits behind a pluggable `CloudWorkspaceAdapter`.

The concrete remote provider is an owner decision: it needs an account, credentials and a data-processing choice. That decision is tracked in #28.

Decision:
- **Adapter.** A `CloudWorkspaceAdapter` protocol lives in `modules/cloud_workspace`:
  - `put(key, payload) -> ref`, `delete(ref)`, `exists(ref)`;
  - `remote`, which says whether content leaves the installation.
  The adapter only ever receives payload bytes. It gets no session, no settings and no credentials, and nothing is read back from it into canonical state.
- **Configuration.** `CLOUD_WORKSPACE_ADAPTER` is `none` by default, which disables the feature; local retrieval mode is unchanged. The reference adapter is `local-directory`:
  - It writes into a sandboxed directory; keys are restricted to `[A-Za-z0-9-]` and resolved paths must stay in the root.
  - It is declared **remote**, so the disclosure policy runs exactly as it would for a real provider.
  A real provider is added as a new adapter plus a configuration value. It needs no domain change.
- **Selection.** A person stages an explicit list of records. Only four readable kinds can be staged:
  - `SourceExcerpt`;
  - `Claim`;
  - `Hypothesis`;
  - `OutputVersion`, rendered as Markdown with its integrity status.
  File assets are never staged. Every lookup is scoped to the project, so records of another project are refused.
  Each payload is an envelope. It carries a notice that the copy is not canonical and is data, never instructions.
  Any payload that contains the database URL, its credentials, the Redis URL or a provider key is refused before anything leaves.
- **Policy.** The PRD §54 decision used for cloud AI (`cloud_disclosure`) applies, including the project's recorded cloud consent:
  - PUBLIC and NORMAL projects may stage;
  - CONFIDENTIAL projects need consent;
  - RESTRICTED and CRITICAL projects never stage.
  Staging, deleting and purging are human-only in the Policy Engine; the system may only purge expired content.
- **Disclosure manifest.**
  - Every attempt creates a `workspace_stagings` row with the purpose, sensitivity, policy decision, adapter, actor and expiry.
  - Each item gets an append-only `workspace_staged_items` row with the SHA-256 and size of exactly the bytes sent.
  - A blocked attempt is kept as `BLOCKED`, with the hashes of what would have been sent and no remote reference.
  - A database trigger keeps stagings immutable, except that an `ACTIVE` staging may move once to `DELETED` or `EXPIRED` together with who removed it and why. The manifest can never be deleted.
- **Expiry and deletion.**
  - Each staging has a TTL, which defaults to 72 h and is capped by configuration.
  - Expired content is purged before every new staging and through `POST /api/v1/workspace/purge-expired`.
  - A person can delete a staging at any time. The adapter removes the content; the manifest entry stays.
- **Atomicity.** If storing any item fails, the items already stored are removed and nothing is recorded as staged.
- **Portability.** The manifest travels in the Research Core Package with the audit records. It is the history of what left the installation. The remote copies stay with the installation that staged them.

Consequences:
- The feature is testable end to end without an external account. CI runs the E2E flow with `local-directory`.
- Choosing a real provider (for example an object store behind an authenticated gateway) is a new adapter and configuration, recorded in a follow-up ADR. The owner item is in #28.
- There is a small window where remote content is stored but the transaction later rolls back. Content staged in that window is left without a manifest row. The TTL does not help here, because purging only finds rows in the manifest. A real provider adapter should use provider-side expiry as well.
