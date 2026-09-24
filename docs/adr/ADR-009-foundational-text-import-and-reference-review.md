# ADR-009: Foundational text import, approval, and layered reference review
Status: Accepted
Date: 2026-09-24

Context:
Core §30 and FR-QURAN-001 require exact Qur'anic text to come from an approved structured source and never from model memory. FR-REFSRC-002/003 forbid AI from adopting foundational sources; adoption needs authorized human approval. Core §7 and FR-REF-001/006 require source text, approved interpretation, system synthesis and practical judgment to stay separate. The product ships without any Qur'an or Hadith content: that content is a constitutional choice, not an engineering one.

Decision:
Foundational library
- `foundational_sources` records authority layer, edition/version, sha256, status (STAGED → APPROVED → RETIRED) and approver. Only the Constitutional Authority can stage or approve; approval is a human-only action (ADR-006). At most one APPROVED Qur'an text exists (partial unique index); approving a new one retires the previous one.
- Qur'an text is imported from a UTF-8 dataset (Tanzil-compatible `surah|ayah|text` lines plus `@surah|n|name` lines). Validation is structural only (numbering 1-114, contiguous ayat, uniqueness, non-empty text, names present). Text is stored byte-for-byte: no trimming, normalization or re-encoding. Rows are append-only (trigger). Staged text is never served.
- Retrieval (`GET /api/v1/reference/quran/{surah}/{ayah}`) returns surah number and name, ayah number, exact text and source id/version/sha256 from the approved dataset only.
- Hadith records belong to an APPROVED Sunnah/foundational source; each record is one narration; numbers are unique per (source, numbering scheme), so different editions keep their own numbering. Records are append-only.

Reference review
- A review targets a claim/hypothesis/mechanism and names an analytical category (Core §6). Entries are append-only and carry a layer:
  - SOURCE_TEXT content is copied server-side from the cited Qur'an reference, Hadith record or source excerpt; clients cannot supply it.
  - APPROVED_INTERPRETATION must cite an excerpt from a work with an APPROVED foundational record.
  - AI-authored entries can only be SYSTEM_SYNTHESIS (service rule + DB CHECK + contract).
- Judgments are human-only and append-only; the latest per review is current. REFERENCE_SUPPORTED needs cited source text and DIRECT/CLOSE directness; NOT_IN_CONFLICT remains distinct. Interpretation divergence is recorded as RESERVED with both readings and the required authority. A BLOCKING_RESERVATION raises a blocking Decision.
- Reference Gate: per target, from latest judgments; missing review is PASS_WITH_RESERVATIONS at L1, NEEDS_HUMAN_DECISION at L2 and BLOCKED at L3/L4. Hypothesis design eligibility requires the Reference Gate to be PASS or PASS_WITH_RESERVATIONS.
- Operational constraints live in their own module and table and are shown beside, never merged with, the reference standing.

Alternatives considered:
- Bundling a Qur'an dataset in the repository: would make an engineering artifact the de facto approved source; rejected.
- Letting clients post source text with a citation: invites paraphrase drift; rejected in favour of server-side copying.

Consequences:
- Until the Constitutional Authority imports and approves a dataset, Qur'an retrieval returns 404 with an explanatory message. This is intentional.
- Tests use synthetic placeholder text only.

Research Core impact: Implements Core §4, §6-9, §29-31, §74.1-3, §74.8-9, §74.25-28.

Migration impact: Migration 0007 adds the tables and append-only triggers.
