# ADR-021: Output integrity pipeline and export
Status: Accepted
Date: 2026-09-24

Context:
FR-OUT-002 requires an eight-step pipeline before an output is final, and FR-OUT-003 requires that language editing comes after quote verification and never changes a protected quote. FR-OUT-006 requires Markdown and HTML export (DOCX and PDF later). CLAUDE.md requires that policy is enforced in code, that AI text is never evidence, and that exact quotes are immutable.

Decision:
- **Pipeline** (`outputs_integrity/pipeline.py`). It runs in order on one output version. Each step returns PASS, WARN, FAIL or SKIPPED, with findings that point to the block index. The steps are:
  1. **Claim verification**: traced research targets exist. A claim reworded away from its record, a claim of WEAK or UNSUBSTANTIATED standing, and a REFUTED hypothesis stated as a claim are warnings.
  2. **Citation verification**: EVIDENCE blocks must cite existing, ACCEPTED evidence. Candidates fail.
  3. **Exact quote verification**: every quote is re-read from its excerpt, the approved Qur'an text, or its Hadith record, and must match byte for byte.
  4. **Reference integrity**: a SOURCE_TEXT layer must be a quote, and interpretation or inference is never shown as a quote.
  5. **Terminology check**: claims whose wording differs from the record are checked against approved terms (ADR-018).
  6. **Translation-semantic check**: the same reworded claims are screened for strength drift (ADR-018). Source language is the project's primary language; target language is the output's.
  7. **Language editing**: for edited versions, no protected quote differs from the previous version.
  8. **Final rendering**: the document is rendered, and every quote line must appear verbatim.
- **Overall status and approval.**
  - Overall: any FAIL → FAILED; any WARN → VERIFIED_WITH_WARNINGS; otherwise VERIFIED.
  - Runs are stored append-only (`output_integrity_runs`).
  - Approval runs the pipeline again. FAILED cannot be approved even with an acknowledgement. VERIFIED_WITH_WARNINGS requires `acknowledge_warnings` and a reason, and is recorded as OVERRIDDEN_WITH_REASON.
- **Edited versions.** `output_versions.edited` marks versions produced by a revision, so step 7 runs only for them. Revisions already refuse changed quotes. Step 7 is defence in depth, for example for data imported by other routes.
- **Export** (`outputs_integrity/render.py`).
  - Markdown and HTML render from the stored blocks. Quotes are emitted verbatim: Markdown blockquote lines; escaped HTML text that unescapes to the exact source.
  - Arabic output renders right-to-left, and Qur'an quotes use the Qur'anic font.
  - REFERENCED and AUDIT copies carry a numbered reference list built only from the records: work authors, title, edition and location; the Qur'an reference with surah name and approved edition; the Hadith collection, book and number.
  - Any copy that is not a VERIFIED, APPROVED version, and every AUDIT copy, carries an integrity footer. An unchecked draft says NOT_CHECKED.
  - The web app proxies downloads through a server route, so the browser never learns the API URL.

Consequences:
- Contracts 0.12.0 add IntegrityRun, IntegrityStepResult, IntegrityFinding and three enums.
- E2E flow 7 covers generating a referenced output.
- DOCX and PDF exports stay open under #45's "after" scope. They can build on the same renderer.
