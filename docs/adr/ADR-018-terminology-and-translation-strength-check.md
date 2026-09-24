# ADR-018: Canonical terminology and the translation strength check
Status: Accepted
Date: 2026-09-24

Context:
PRD §36 and Core §53 require:
- canonical terminology records: term, domain, definition, ar/fr/en translations, alternatives, a retain-original preference, and source/authority;
- a translation integrity check that detects claims strengthened or weakened in translation, such as association becoming causation (FR-TERM-003).
The Phase 5 output pipeline runs this check as its terminology and translation-semantic steps (FR-OUT-002 steps 5-6). A model must not be the only judge of this; the check must be testable and repeatable.

Decision:
- **Terms** are library-wide and versioned (`terms`, series plus version_number plus supersedes_id).
  - Content is immutable (DB trigger). Only forward status moves are allowed: PROPOSED → APPROVED/REJECTED/SUPERSEDED, APPROVED → SUPERSEDED. The approver is stamped once at approval. Terms cannot be deleted.
  - Anyone, including the AI with provenance, may propose a term or a revision.
  - Only a human with the Methodology Steward or Constitutional Authority role can approve or reject a term (`term.approve`/`term.reject`).
  - Approving a version supersedes the previously approved version in its series. A pending revision leaves the approved version canonical.
- **Claim-strength screen** (`knowledge_memory/claim_strength.py`) is deterministic. A curated lexicon for ar, fr and en profiles each text on three ordinal axes:
  - relation: NONE < ASSOCIATIVE < CAUSAL;
  - certainty: HEDGED < NEUTRAL < CERTAIN;
  - scope: PARTIAL < NEUTRAL < UNIVERSAL.
  Comparing the source and translation profiles gives STRENGTHENED or WEAKENED findings with the matched markers.
  - Arabic text is normalised: diacritics and tatweel are removed and letter variants are folded. Markers then match inside words, because attached particles would otherwise hide them. Short particles such as قد match only as whole words.
  - Latin-script text is case-folded and accent-stripped. Markers match whole words; a `stem*` marker covers inflected forms.
  - Mixed certainty or scope signals are left NEUTRAL rather than guessed.
- **Terminology check.** For each approved term (optionally filtered by domain) whose source-language form appears in the source, the translation must contain one of: the approved target translation, a target-language alternative, or the original term if it is marked retain-original.
- `POST /api/v1/integrity/translation-check` returns both results and a `passed` flag. It is stateless. The outcome is presented as a screen for a person to review, not as proof of fidelity. Phase 5 will record it in the output integrity pipeline.

Consequences:
- Contracts 0.10.0 add `terminology.schema.json` (Term) and the TermStatus enum.
- The lexicon is data in code, covered by multilingual fixtures. Extending it is a reviewed code change, like other policy rules (CLAUDE.md: rules are code/config, not prompts).
